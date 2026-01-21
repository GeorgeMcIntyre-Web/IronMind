from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from optiforge.core.models import ProblemSpec


class ChatProvider(Protocol):
    def generate_ir(self, spec: ProblemSpec) -> dict[str, Any]:
        ...


class OpenAIChatProvider:
    def __init__(self, base_url: str, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("provider_api_key is required for the openai provider")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._client = httpx.Client(timeout=30.0)

    def generate_ir(self, spec: ProblemSpec) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": _build_messages(spec),
            "temperature": 0.0,
        }
        response = self._client.post(
            f"{self._base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
        )
        if response.status_code >= 400:
            raise ValueError(f"provider error: {response.status_code}")
        data = response.json()
        choices = data.get("choices")
        if not choices:
            raise ValueError("provider response missing choices")
        message = choices[0].get("message")
        if not message:
            raise ValueError("provider response missing message")
        content = message.get("content")
        if not content:
            raise ValueError("provider response missing content")
        cleaned = _extract_json(content)
        return json.loads(cleaned)


class StubProvider:
    def generate_ir(self, spec: ProblemSpec) -> dict[str, Any]:
        _ = spec
        return {
            "version": "1.0",
            "name": "stub_min_cost",
            "description": "Deterministic stub IR",
            "variables": [
                {"name": "x", "type": "int", "lower_bound": 0, "upper_bound": 10},
                {"name": "y", "type": "int", "lower_bound": 0, "upper_bound": 10},
            ],
            "constraints": [
                {
                    "type": "linear",
                    "terms": [
                        {"var": "x", "coeff": 1},
                        {"var": "y", "coeff": 1},
                    ],
                    "operator": ">=",
                    "rhs": 5,
                }
            ],
            "objective": {
                "sense": "minimize",
                "terms": [
                    {"var": "x", "coeff": 3},
                    {"var": "y", "coeff": 2},
                ],
                "constant": 0,
            },
        }


def get_provider(provider: str, base_url: str, api_key: str | None, model: str) -> ChatProvider:
    if provider == "stub":
        return StubProvider()
    if provider == "openai":
        return OpenAIChatProvider(base_url=base_url, api_key=api_key, model=model)
    raise ValueError(f"unknown provider: {provider}")


def _build_messages(spec: ProblemSpec) -> list[dict[str, str]]:
    instruction = (
        "Return ONLY valid JSON matching the OptimizationModelIR schema. "
        "Use integer coefficients and bounds."
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(spec.model_dump(), ensure_ascii=True)},
    ]


def _extract_json(content: str) -> str:
    if "```" not in content:
        return content.strip()
    lines = []
    for line in content.splitlines():
        if line.strip().startswith("```"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()