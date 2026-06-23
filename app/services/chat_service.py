"""Chat service: orchestrates the Strands agent, SSE streaming, and approval flow.

This is the central service that ties together the agent, database persistence,
and the streaming protocol.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.factory import create_agent
from app.models.chat import ActionStatus, ChatMessage, ChatSession, MessageRole
from app.repositories.chat_repo import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._chat_repo = ChatRepository(db)

    async def stream_chat(
        self,
        session_id: str,
        message: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream agent response as structured events for SSE.

        Yields dicts with a 'type' key indicating the event kind:
        - text: streaming text content
        - tool_start: tool execution beginning
        - tool_end: tool execution complete
        - approval_required: action needs user approval
        - done: stream complete
        """
        session = await self._chat_repo.get_by_id(session_id)
        if session is None:
            title = message[:80] if len(message) > 80 else message
            session = await self._chat_repo.create_session(session_id, title=title)

        await self._chat_repo.add_message(session_id, MessageRole.USER, message)
        await self._db.commit()

        agent = create_agent(session_id)
        full_response = ""
        active_tool: str | None = None

        try:
            async for event in agent.stream_async(message):
                # Text content streaming
                if "data" in event:
                    chunk = event["data"]
                    full_response += chunk
                    yield {"type": "text", "content": chunk}

                # Tool usage tracking
                if "current_tool_use" in event:
                    tool_info = event["current_tool_use"]
                    tool_name = tool_info.get("name")
                    if tool_name and tool_name != active_tool:
                        if active_tool:
                            yield {"type": "tool_end", "tool": active_tool}
                        active_tool = tool_name
                        yield {
                            "type": "tool_start",
                            "tool": tool_name,
                            "input": tool_info.get("input", {}),
                        }

                # Agent result (final event)
                if "result" in event:
                    result = event["result"]
                    if active_tool:
                        yield {"type": "tool_end", "tool": active_tool}
                        active_tool = None

                    stop_reason = str(result.stop_reason) if result.stop_reason else "end_turn"

                    if stop_reason == "interrupt" and hasattr(result, "interrupts"):
                        for interrupt in result.interrupts:
                            reason = interrupt.reason if hasattr(interrupt, "reason") else {}
                            interrupt_id = interrupt.id if hasattr(interrupt, "id") else ""
                            action = reason.get("action", "") if isinstance(reason, dict) else ""
                            params = reason.get("params", {}) if isinstance(reason, dict) else {}
                            preview = reason.get("preview", "") if isinstance(reason, dict) else str(reason)

                            # Persist a PENDING action so approval is idempotent
                            # (exactly-once via CAS status transitions on resume).
                            if interrupt_id and action:
                                await self._persist_pending_action(
                                    action_id=interrupt_id,
                                    session_id=session_id,
                                    tool_name=action,
                                    params=params if isinstance(params, dict) else {},
                                    preview=preview,
                                )

                            yield {
                                "type": "approval_required",
                                "interrupt_id": interrupt_id,
                                "action": action,
                                "params": params,
                                "preview": preview,
                                "session_id": session_id,
                            }
                    else:
                        yield {
                            "type": "done",
                            "session_id": session_id,
                            "stop_reason": stop_reason,
                        }

        except Exception as e:
            logger.exception("Agent error in session %s: %s", session_id, e)
            yield {"type": "error", "message": str(e)}

        if full_response:
            await self._chat_repo.add_message(session_id, MessageRole.ASSISTANT, full_response)
            await self._db.commit()

    async def _persist_pending_action(
        self,
        action_id: str,
        session_id: str,
        tool_name: str,
        params: dict[str, Any],
        preview: str,
    ) -> None:
        """Record a pending action so its approval can be made idempotent.

        Uses the interrupt id as the action id. If a row already exists (e.g.
        the stream was retried), we leave the existing status untouched.
        """
        existing = await self._chat_repo.get_action_log(action_id)
        if existing is not None:
            return
        await self._chat_repo.create_action_log(
            action_id=action_id,
            session_id=session_id,
            tool_name=tool_name,
            params=params,
            preview=preview,
        )
        await self._db.commit()

    async def handle_approval(
        self,
        session_id: str,
        interrupt_id: str,
        decision: str,
        edited_params: dict[str, object] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Handle user's approval/rejection decision and resume the agent.

        Exactly-once: the action is tracked in `action_log` with CAS status
        transitions (pending -> approved -> executed). A retried approval for
        an already-executed action is a no-op, so the underlying write tool
        never runs twice even if the request is retried or the process restarts.
        """
        if decision == "reject":
            if interrupt_id:
                await self._chat_repo.reject_action(interrupt_id)
                await self._db.commit()
            yield {
                "type": "text",
                "content": "Action rejected. No changes were made.",
            }
            yield {"type": "done", "session_id": session_id, "stop_reason": "rejected"}
            return

        # Idempotency guard: don't re-run an action that already executed.
        if interrupt_id:
            existing = await self._chat_repo.get_action_log(interrupt_id)
            if existing is not None and existing.status == ActionStatus.EXECUTED:
                yield {
                    "type": "text",
                    "content": "This action was already completed. No changes were made.",
                }
                yield {
                    "type": "done",
                    "session_id": session_id,
                    "stop_reason": "already_executed",
                }
                return
            if existing is not None and existing.status == ActionStatus.REJECTED:
                yield {
                    "type": "text",
                    "content": "This action was already rejected. No changes were made.",
                }
                yield {
                    "type": "done",
                    "session_id": session_id,
                    "stop_reason": "already_rejected",
                }
                return
            # CAS pending -> approved. None means another request already moved
            # it past pending; we still resume so an approved-but-not-executed
            # action can complete.
            await self._chat_repo.approve_action(interrupt_id)
            await self._db.commit()

        # Build the interrupt response payload
        if decision == "edit" and edited_params:
            response_data = json.dumps(
                {
                    "decision": "edit",
                    "edited_params": edited_params,
                }
            )
        else:
            response_data = "approved"

        interrupt_response = [
            {
                "interruptResponse": {
                    "interruptId": interrupt_id,
                    "response": response_data,
                }
            }
        ]

        agent = create_agent(session_id)
        full_response = ""
        active_tool: str | None = None

        try:
            async for event in agent.stream_async(interrupt_response):
                if "data" in event:
                    chunk = event["data"]
                    full_response += chunk
                    yield {"type": "text", "content": chunk}

                if "current_tool_use" in event:
                    tool_info = event["current_tool_use"]
                    tool_name = tool_info.get("name")
                    if tool_name and tool_name != active_tool:
                        if active_tool:
                            yield {"type": "tool_end", "tool": active_tool}
                        active_tool = tool_name
                        yield {
                            "type": "tool_start",
                            "tool": tool_name,
                            "input": tool_info.get("input", {}),
                        }

                if "result" in event:
                    if active_tool:
                        yield {"type": "tool_end", "tool": active_tool}
                    # CAS approved -> executed marks exactly-once completion.
                    if interrupt_id:
                        await self._chat_repo.mark_executed(interrupt_id)
                        await self._db.commit()
                    yield {
                        "type": "done",
                        "session_id": session_id,
                        "stop_reason": "end_turn",
                    }

        except Exception as e:
            logger.exception("Agent resume error in session %s: %s", session_id, e)
            yield {"type": "error", "message": str(e)}

        if full_response:
            await self._chat_repo.add_message(session_id, MessageRole.ASSISTANT, full_response)
            await self._db.commit()

    async def list_sessions(self, *, limit: int = 50, offset: int = 0) -> list[ChatSession]:
        return await self._chat_repo.list_sessions(limit=limit, offset=offset)

    async def session_exists(self, session_id: str) -> bool:
        return await self._chat_repo.get_by_id(session_id) is not None

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        return await self._chat_repo.get_messages(session_id)
