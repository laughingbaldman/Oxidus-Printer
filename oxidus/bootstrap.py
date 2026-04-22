from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


def ensure_runtime_dependencies(requirements_path: Path, modules: Iterable[str]) -> None:
    missing_modules = [module for module in modules if importlib.util.find_spec(module) is None]
    if not missing_modules:
        return

    env = os.environ.copy()
    env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        env=env,
    )
    importlib.invalidate_caches()