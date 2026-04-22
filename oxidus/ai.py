from __future__ import annotations

import json
from dataclasses import dataclass

import requests

from .models import PrinterSpec
from .parts_catalog import ResolvedPartSpec


@dataclass(frozen=True)
class AISettings:
    enabled: bool
    base_url: str
    model: str
    timeout_seconds: int = 20


def _build_prompt(spec: PrinterSpec, parts: list[ResolvedPartSpec]) -> str:
    parts_summary = [
        {
            "name": part.name,
            "category": part.category,
            "material": part.material,
            "supplier": part.supplier.name,
            "qty": part.qty,
        }
        for part in parts
    ]
    payload = {
        "project": "Oxidus Print!",
        "goal": "Generate a concise builder recommendation with practical intuition.",
        "printer": {
            "x_mm": spec.x_mm,
            "y_mm": spec.y_mm,
            "z_mm": spec.z_mm,
            "volume_liters": round(spec.volume_liters, 2),
        },
        "parts": parts_summary,
        "instructions": [
            "Respond in JSON with keys summary, watchouts, recommended_materials, next_step.",
            "Keep summary under 90 words.",
            "Each list should contain 2 to 4 concise items.",
        ],
    }
    return json.dumps(payload)


def generate_ai_recommendation(
    spec: PrinterSpec,
    parts: list[ResolvedPartSpec],
    settings: AISettings,
) -> dict[str, object]:
    if not settings.enabled:
        return {
            "summary": "AI intuition is disabled. Enable the network inference endpoint to generate build recommendations.",
            "watchouts": [],
            "recommended_materials": [],
            "next_step": "Review the generated build sheet and STL starter parts.",
            "status": "disabled",
        }

    if not settings.base_url.strip():
        return {
            "summary": "No AI endpoint is configured yet. Set the network inference URL to enable GPTOSS20B recommendations.",
            "watchouts": [],
            "recommended_materials": [],
            "next_step": "Enter an OpenAI-compatible network endpoint for your GPTOSS20B deployment.",
            "status": "unconfigured",
        }

    endpoint = settings.base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": settings.model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert 3D printer architect helping size a Voron-inspired machine. Be concrete, terse, and practical.",
            },
            {
                "role": "user",
                "content": _build_prompt(spec, parts),
            },
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(endpoint, json=body, timeout=settings.timeout_seconds)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    parsed["status"] = "ok"
    return parsed
