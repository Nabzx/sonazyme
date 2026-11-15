"""Schema-driven Tamarind job submission for the design stage."""

from __future__ import annotations

from typing import Protocol

from sonazyme.api.tamarind import TamarindClient


class DesignJobClient(Protocol):
    """The Tamarind operations needed for one design submission."""

    def list_tools(self) -> list[dict]:
        """Return the account's live tool catalog."""
        ...

    def validate_job(
        self,
        tool: str,
        settings: dict,
        *,
        job_name: str | None = None,
    ) -> dict:
        """Validate one job without submitting it."""
        ...

    def submit_job(self, job_name: str, tool: str, settings: dict) -> str:
        """Submit a validated job."""
        ...


def submit_design_job(
    job_name: str,
    tool_name: str,
    settings: dict,
    *,
    client: DesignJobClient | None = None,
) -> str:
    """Discover, preflight and submit one explicitly selected Tamarind tool."""
    client = client or TamarindClient()
    if not isinstance(settings, dict):
        raise ValueError("Tamarind settings must be an object.")
    tool = next((item for item in client.list_tools() if item.get("name") == tool_name), None)
    if tool is None:
        raise ValueError(f"Tamarind does not list the requested tool: {tool_name}")
    if tool.get("finetune") is True:
        raise ValueError("A finetuning tool must use Tamarind's finetune endpoint.")
    schema = tool.get("settings")
    if not isinstance(schema, list):
        raise ValueError(f"Tamarind returned no settings schema for {tool_name}.")
    if any(not isinstance(item, dict) or not isinstance(item.get("name"), str) for item in schema):
        raise ValueError(f"Tamarind returned an invalid settings schema for {tool_name}.")
    names = {item["name"] for item in schema}
    unknown = set(settings) - names
    if unknown:
        raise ValueError(f"Unknown settings for {tool_name}: {', '.join(sorted(unknown))}")
    resolved = dict(settings)
    for item in schema:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        name = item["name"]
        if name not in resolved and item.get("default") is not None:
            resolved[name] = item["default"]
    missing = [
        item["name"]
        for item in schema
        if isinstance(item, dict)
        and item.get("required")
        and item["name"] not in resolved
    ]
    if missing:
        raise ValueError(f"Missing required settings for {tool_name}: {', '.join(missing)}")
    validation = client.validate_job(tool_name, resolved, job_name=job_name)
    if validation.get("valid") is not True:
        raise ValueError(
            f"Tamarind rejected the job settings: {validation.get('error', 'invalid settings')}"
        )
    normalized = validation.get("normalized")
    if not isinstance(normalized, dict):
        raise ValueError("Tamarind validation did not return normalized settings.")
    return client.submit_job(job_name, tool_name, normalized)
