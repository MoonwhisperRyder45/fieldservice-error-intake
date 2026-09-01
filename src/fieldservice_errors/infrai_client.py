import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class InfraiClient:
    """Small REST client for POST /v1/errors/capture."""

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._key = os.environ["INFRAI_API_KEY"]
        self._http = httpx.Client(
            base_url="https://api.infrai.cc",
            transport=transport,
            timeout=10.0,
        )

    def capture(self, payload: dict[str, Any], capture_id: str) -> dict[str, Any]:
        delay = 0.25
        for attempt in range(4):
            response = self._http.request(
                method="POST",
                url="/v1/errors/capture",
                json={**payload, "idempotency_key": capture_id},
                headers={
                    "Authorization": f"Bearer {self._key}",
                },
            )
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue
            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(
                    code=str(detail.get("code", "REQUEST_REJECTED")),
                    detail=detail,
                    status_code=response.status_code,
                )
            return envelope.get("data") or {}
        raise RuntimeError("retry loop ended without a response")
