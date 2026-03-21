"""HTTP client for BoldSign template send (REST v1)."""

import json
from typing import Any

import requests

from backend.exceptions import BoldSignServiceError


class BoldSignTemplateClient:
    """Send-from-template API call; keeps timeouts and error mapping in one place."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        session: requests.Session | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._session = session if session is not None else requests.Session()
        self._timeout_seconds = timeout_seconds

    def send_template(self, template_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}/v1/template/send"
        headers = {
            "accept": "application/json",
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json;odata.metadata=minimal;odata.streaming=true",
        }
        response = self._session.post(
            url,
            params={"templateId": template_id},
            headers=headers,
            data=json.dumps(payload),
            timeout=self._timeout_seconds,
        )
        if response.status_code != 201:
            try:
                err_body = response.json()
                err_msg = err_body.get("error", err_body.get("message", response.text))
            except Exception:
                err_msg = response.text or f"HTTP {response.status_code}"
            raise BoldSignServiceError(err_msg, code="boldsign_http_error") from None
        return response.json()
