"""Server-side client for Tamarind's job API."""

from __future__ import annotations

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://app.tamarind.bio/api/"
_JOB_NAME = re.compile(r"[A-Za-z0-9_.-]{1,200}\Z")


class TamarindAPIError(RuntimeError):
    """A failed or malformed Tamarind API request."""


class TamarindClient:
    """Discover, validate and submit jobs using a server-side API key."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30,
    ) -> None:
        """Create a client from an explicit key or `TAMARIND_API_KEY`."""
        key = api_key if api_key is not None else os.environ.get("TAMARIND_API_KEY")
        if not key or not key.strip():
            raise RuntimeError("Set TAMARIND_API_KEY in the server environment.")
        self._api_key = key.strip()
        self._base_url = base_url.rstrip("/") + "/"
        self._timeout = timeout

    def list_tools(self) -> list[dict]:
        """Return the account's live tool catalog and settings schemas."""
        result = self._json_request("GET", "tools")
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise TamarindAPIError("Tamarind returned an invalid tool catalog.")
        return result

    def get_tool_schema(self, name: str) -> dict:
        """Return the live JSON Schema for a tool."""
        result = self._json_request("GET", f"tools/{quote(name, safe='')}/schema")
        if not isinstance(result, dict):
            raise TamarindAPIError("Tamarind returned an invalid tool schema.")
        return result

    def validate_job(
        self,
        tool: str,
        settings: dict,
        *,
        job_name: str | None = None,
    ) -> dict:
        """Preflight settings without submitting or consuming a job."""
        payload = {"type": tool, "settings": settings}
        if job_name is not None:
            _validate_job_name(job_name)
            payload["jobName"] = job_name
        result = self._json_request("POST", "validate-job", payload)
        if not isinstance(result, dict):
            raise TamarindAPIError("Tamarind returned an invalid validation response.")
        return result

    def submit_job(self, job_name: str, tool: str, settings: dict) -> str:
        """Submit a job that has already passed validation."""
        _validate_job_name(job_name)
        if not tool or not isinstance(settings, dict):
            raise ValueError("A Tamarind tool and settings object are required.")
        _, body = self._request(
            "POST",
            "submit-job",
            {"jobName": job_name, "type": tool, "settings": settings},
        )
        return body.decode("utf-8", "replace")

    def get_job(self, job_name: str) -> dict:
        """Return the status for one job name."""
        _validate_job_name(job_name)
        result = self._json_request("GET", "jobs?" + urlencode({"jobName": job_name}))
        if not isinstance(result, dict):
            raise TamarindAPIError("Tamarind returned an invalid job response.")
        return result

    def result_url(self, job_name: str, *, file_name: str | None = None) -> str | None:
        """Return a result download URL, or None while Tamarind prepares it."""
        _validate_job_name(job_name)
        payload = {"jobName": job_name}
        if file_name is not None:
            payload["fileName"] = file_name
        status, body = self._request("POST", "result", payload)
        if status == 202:
            return None
        try:
            url = json.loads(body)
        except json.JSONDecodeError as error:
            raise TamarindAPIError("Tamarind returned an invalid result URL.") from error
        if not isinstance(url, str) or not url.startswith("https://"):
            raise TamarindAPIError("Tamarind returned an unsafe result URL.")
        return url

    def download_result(self, url: str) -> bytes:
        """Download a presigned result without forwarding the Tamarind API key."""
        if not url.startswith("https://"):
            raise ValueError("A result download URL must use HTTPS.")
        request = Request(url, headers={"Accept": "application/octet-stream"})
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.getcode()
                if status < 200 or status >= 300:
                    raise TamarindAPIError(f"Result download failed with HTTP {status}.")
                return response.read()
        except HTTPError as error:
            raise TamarindAPIError(
                f"Result download failed with HTTP {error.code}."
            ) from None
        except URLError as error:
            raise TamarindAPIError("Could not reach the result download host.") from error

    def _json_request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
    ) -> object:
        _, body = self._request(method, path, payload)
        try:
            return json.loads(body)
        except json.JSONDecodeError as error:
            raise TamarindAPIError(f"Tamarind returned invalid JSON for {path}.") from error

    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
    ) -> tuple[int, bytes]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json", "x-api-key": self._api_key}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self._base_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.getcode()
                body = response.read()
        except HTTPError as error:
            raise TamarindAPIError(
                f"Tamarind request failed with HTTP {error.code} for {method} {path}."
            ) from None
        except URLError as error:
            raise TamarindAPIError("Could not reach the Tamarind API.") from error
        if status < 200 or status >= 300:
            raise TamarindAPIError(f"Tamarind request failed with HTTP {status} for {path}.")
        return status, body


def _validate_job_name(job_name: str) -> None:
    if not isinstance(job_name, str) or not _JOB_NAME.fullmatch(job_name):
        raise ValueError(
            "Tamarind job names must be 1–200 letters, digits, dots, underscores or hyphens."
        )
