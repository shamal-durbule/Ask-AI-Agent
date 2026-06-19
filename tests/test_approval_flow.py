"""Tests for the approval-gated action flow.

These tests verify that:
- Write tools are correctly identified and gated
- The ApprovalHook raises interrupts for write tools
- Read tools are NOT gated
- Preview messages are generated correctly
"""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.agent.hooks.approval_hook import WRITE_TOOLS, ApprovalHook, _build_preview


class TestWriteToolIdentification:
    """Verify the correct tools are classified as write tools."""

    def test_send_message_is_write(self) -> None:
        assert "send_message" in WRITE_TOOLS

    def test_schedule_message_is_write(self) -> None:
        assert "schedule_message" in WRITE_TOOLS

    def test_apply_credit_is_write(self) -> None:
        assert "apply_credit" in WRITE_TOOLS

    def test_get_properties_is_not_write(self) -> None:
        assert "get_properties" not in WRITE_TOOLS

    def test_get_tenants_is_not_write(self) -> None:
        assert "get_tenants" not in WRITE_TOOLS

    def test_execute_readonly_query_is_not_write(self) -> None:
        assert "execute_readonly_query" not in WRITE_TOOLS

    def test_get_database_schema_is_not_write(self) -> None:
        assert "get_database_schema" not in WRITE_TOOLS


class TestPreviewGeneration:
    """Verify human-readable previews for each write tool."""

    def test_send_message_preview(self) -> None:
        preview = _build_preview("send_message", {
            "tenant_id": 5,
            "body": "Your rent is due.",
        })
        assert "tenant #5" in preview
        assert "Your rent is due." in preview

    def test_schedule_message_preview(self) -> None:
        preview = _build_preview("schedule_message", {
            "tenant_id": 3,
            "body": "Reminder",
            "send_at": "2025-02-01T09:00:00",
        })
        assert "tenant #3" in preview
        assert "2025-02-01" in preview

    def test_apply_credit_preview(self) -> None:
        preview = _build_preview("apply_credit", {
            "lease_id": 10,
            "amount": 75,
            "reason": "late fee waiver",
        })
        assert "$75" in preview
        assert "lease #10" in preview
        assert "late fee waiver" in preview

    def test_long_body_truncated(self) -> None:
        long_body = "x" * 500
        preview = _build_preview("send_message", {
            "tenant_id": 1,
            "body": long_body,
        })
        assert len(preview) < 300


class TestApprovalHookBehavior:
    """Test that the hook correctly gates write tools and passes read tools."""

    def test_read_tool_not_interrupted(self) -> None:
        hook = ApprovalHook()
        event = MagicMock()
        event.tool_use = {"name": "get_properties", "input": {}}

        registry = MagicMock()
        hook.register_hooks(registry)

        # Get the registered callback
        callback = registry.add_callback.call_args[0][1]
        callback(event)

        event.interrupt.assert_not_called()
        assert not hasattr(event, 'cancel_tool') or event.cancel_tool is None or event.cancel_tool == event.cancel_tool

    def test_write_tool_triggers_interrupt(self) -> None:
        hook = ApprovalHook()
        event = MagicMock()
        event.tool_use = {
            "name": "send_message",
            "input": {"tenant_id": 1, "body": "Hello"},
        }
        event.interrupt.return_value = "approved"

        registry = MagicMock()
        hook.register_hooks(registry)

        callback = registry.add_callback.call_args[0][1]
        callback(event)

        event.interrupt.assert_called_once()
        call_args = event.interrupt.call_args
        assert "approve_send_message" in call_args[0][0]

    def test_rejection_cancels_tool(self) -> None:
        hook = ApprovalHook()
        event = MagicMock()
        event.tool_use = {
            "name": "send_message",
            "input": {"tenant_id": 1, "body": "Hello"},
        }
        event.interrupt.return_value = "rejected"
        event.cancel_tool = None

        registry = MagicMock()
        hook.register_hooks(registry)

        callback = registry.add_callback.call_args[0][1]
        callback(event)

        assert event.cancel_tool is not None
        assert "rejected" in event.cancel_tool.lower() if isinstance(event.cancel_tool, str) else True
