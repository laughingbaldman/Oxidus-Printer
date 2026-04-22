from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
from typing import Any

import requests


@dataclass(frozen=True)
class TargetConfig:
    backend: str
    base_url: str
    api_key: str
    auto_start: bool


def normalize_base_url(value: str) -> str:
    url = value.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url.rstrip("/")


def command_available(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def _build_command(
    template: str,
    command: str,
    input_model: Path,
    output_gcode: Path,
) -> list[str]:
    rendered = template.format(
        orca_cmd=command,
        input_stl=str(input_model),
        input_model=str(input_model),
        output_gcode=str(output_gcode),
    )
    return shlex.split(rendered)


def slice_with_orca(
    model_bytes: bytes,
    model_filename: str,
    command: str,
    template: str,
) -> tuple[bytes, str, str]:
    with tempfile.TemporaryDirectory(prefix="oxidus_orca_") as temp_dir:
        temp = Path(temp_dir)
        model_path = temp / model_filename
        gcode_path = temp / f"{model_path.stem}.gcode"
        model_path.write_bytes(model_bytes)

        cmd = _build_command(
            template=template,
            command=command,
            input_model=model_path,
            output_gcode=gcode_path,
        )
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        log = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")

        if proc.returncode != 0:
            raise RuntimeError(f"Orca slicing failed with exit code {proc.returncode}.\n{log}")
        if not gcode_path.exists():
            raise RuntimeError(
                "Orca command completed but no output gcode was found. "
                "Check your command template and Orca CLI flags."
            )

        return gcode_path.read_bytes(), gcode_path.name, log.strip()


def send_to_octoprint(
    config: TargetConfig,
    gcode_bytes: bytes,
    gcode_filename: str,
) -> dict[str, Any]:
    headers = {}
    if config.api_key:
        headers["X-Api-Key"] = config.api_key

    response = requests.post(
        f"{config.base_url}/api/files/local",
        headers=headers,
        files={"file": (gcode_filename, gcode_bytes, "application/octet-stream")},
        data={
            "select": "true",
            "print": "true" if config.auto_start else "false",
        },
        timeout=30,
    )
    response.raise_for_status()

    return {
        "status": "ok",
        "backend": "OctoPrint",
        "http_status": response.status_code,
        "response": response.json() if response.content else {},
    }


def send_to_moonraker(
    config: TargetConfig,
    gcode_bytes: bytes,
    gcode_filename: str,
) -> dict[str, Any]:
    upload = requests.post(
        f"{config.base_url}/server/files/upload",
        files={"file": (gcode_filename, gcode_bytes, "application/octet-stream")},
        data={"root": "gcodes"},
        timeout=30,
    )
    upload.raise_for_status()

    start_result: dict[str, Any] = {}
    if config.auto_start:
        start = requests.post(
            f"{config.base_url}/printer/print/start",
            json={"filename": gcode_filename},
            timeout=20,
        )
        start.raise_for_status()
        start_result = start.json() if start.content else {}

    return {
        "status": "ok",
        "backend": "Moonraker",
        "http_status": upload.status_code,
        "upload_response": upload.json() if upload.content else {},
        "print_start_response": start_result,
    }


def send_gcode(
    config: TargetConfig,
    gcode_bytes: bytes,
    gcode_filename: str,
) -> dict[str, Any]:
    if config.backend == "OctoPrint":
        return send_to_octoprint(config, gcode_bytes, gcode_filename)
    if config.backend == "Moonraker":
        return send_to_moonraker(config, gcode_bytes, gcode_filename)
    raise ValueError(f"Unsupported backend: {config.backend}")
