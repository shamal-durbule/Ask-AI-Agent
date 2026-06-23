"""Approval hook that intercepts data-changing tools via Strands interrupts.

Write tools are gated behind human approval. When the agent tries to call
a write tool, this hook raises an interrupt, pausing the agent until the
user approves, rejects, or edits the action.
"""

import contextlib
import json
import logging
from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

logger = logging.getLogger(__name__)

WRITE_TOOLS = frozenset({"send_message", "schedule_message", "apply_credit"})


def _build_preview(tool_name: str, params: dict[str, Any]) -> str:
    """Build a human-readable preview of the action."""
    if tool_name == "send_message":
        return f'Send message to tenant #{params.get("tenant_id")}: "{params.get("body", "")[:200]}"'
    elif tool_name == "schedule_message":
        return (
            f"Schedule message to tenant #{params.get('tenant_id')} "
            f"for {params.get('send_at')}: "
            f'"{params.get("body", "")[:200]}"'
        )
    elif tool_name == "apply_credit":
        return (
            f"Apply ${params.get('amount', 0)} credit to lease #{params.get('lease_id')}"
            f" (reason: {params.get('reason', 'N/A')})"
        )
    return f"Execute {tool_name} with params: {json.dumps(params, default=str)}"


class ApprovalHook(HookProvider):
    """Intercepts write tool calls and requires human approval via interrupts."""

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self._require_approval)

    def _require_approval(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "")
        if tool_name not in WRITE_TOOLS:
            return

        params = event.tool_use.get("input", {})
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                params = {"raw": params}

        preview = _build_preview(tool_name, params)

        logger.info("Approval required for %s: %s", tool_name, preview)

        response = event.interrupt(
            f"approve_{tool_name}",
            reason={
                "action": tool_name,
                "params": params,
                "preview": preview,
            },
        )

        if isinstance(response, str):
            with contextlib.suppress(json.JSONDecodeError):
                response = json.loads(response)

        if isinstance(response, dict):
            decision = response.get("decision", "reject")
            if decision == "reject":
                event.cancel_tool = "User rejected the action"
                return
            if decision == "edit":
                edited = response.get("edited_params", {})
                if edited and isinstance(event.tool_use.get("input"), dict):
                    event.tool_use["input"].update(edited)
        elif response == "approved":
            return
        elif response == "rejected":
            event.cancel_tool = "User rejected the action"
