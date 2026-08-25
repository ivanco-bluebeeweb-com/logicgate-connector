"""Thin LogicGate Public API REST client.

Auth model: static Bearer API Token (from LogicGate Admin > API Tokens). Base
URL defaults to https://api.logicgate.com but is kept configurable.
"""
from __future__ import annotations

from typing import Any

import httpx

_DEFAULT_BASE = "https://api.logicgate.com"


class LogicGateError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class LogicGateClient:
    """REST client for the LogicGate Public API, scoped to one account."""

    def __init__(
        self,
        api_token: str,
        base_url: str = "",
        *,
        timeout: float = 30.0,
    ):
        if not api_token:
            raise LogicGateError("API Token is required.")
        self.api_token = api_token
        self.base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self.timeout = timeout

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[Any, httpx.Response]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(
                    method, url, params=params, json=json_body, headers=headers,
                )
            except httpx.TimeoutException:
                raise LogicGateError("LogicGate API request timed out.", retryable=True)
            except httpx.HTTPError as exc:
                raise LogicGateError(f"Network error contacting LogicGate: {exc}", retryable=True)

        if resp.status_code in (401, 403):
            raise LogicGateError(
                "Your API Token doesn't have access to this. Check Admin > API Tokens in LogicGate and verify scope/permissions.",
                retryable=False,
            )
        if resp.status_code == 404:
            raise LogicGateError("Not found — check the Application/Record id.", retryable=False)
        if resp.status_code == 429:
            raise LogicGateError("Rate limited by LogicGate. Try again shortly.", retryable=True)
        if resp.status_code >= 500:
            raise LogicGateError("LogicGate API had a server error. Try again shortly.", retryable=True)
        if resp.status_code >= 400:
            raise LogicGateError(f"LogicGate API error ({resp.status_code}): {resp.text[:300]}", retryable=False)

        if not resp.content:
            return None, resp
        try:
            return resp.json(), resp
        except ValueError:
            return None, resp

    @staticmethod
    def unwrap_list(data: Any) -> list[dict]:
        """Tolerantly extract a list of records from varied response envelopes."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("data", "records", "applications", "items", "results"):
                val = data.get(key)
                if isinstance(val, list):
                    return val
        return []
