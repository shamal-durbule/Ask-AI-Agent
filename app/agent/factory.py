"""Agent factory: creates configured Strands Agent instances.

Each chat session gets an agent initialized with the appropriate session
manager for conversation continuity.
"""

import logging
import os
from pathlib import Path

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.session.file_session_manager import FileSessionManager

from app.agent.hooks.approval_hook import ApprovalHook
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tools.analytics_tools import execute_readonly_query, get_database_schema
from app.agent.tools.read_tools import get_leases, get_overdue_charges, get_properties, get_tenants
from app.config import settings

logger = logging.getLogger(__name__)

READ_TOOLS = [get_properties, get_tenants, get_leases, get_overdue_charges]
ANALYTICS_TOOLS = [get_database_schema, execute_readonly_query]

_SKILL_PATH = Path(__file__).parent / "skills" / "analytics" / "SKILL.md"


def _load_analytics_skill() -> str:
    """Load the analytics skill instructions to fold into the system prompt.

    The frontmatter (between the leading '---' fences) is metadata; only the
    instruction body is appended so the agent follows the SQL guidance.
    """
    try:
        raw = _SKILL_PATH.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Analytics skill file not found at %s", _SKILL_PATH)
        return ""

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return raw.strip()


_ANALYTICS_SKILL = _load_analytics_skill()


def _build_system_prompt() -> str:
    if not _ANALYTICS_SKILL:
        return SYSTEM_PROMPT
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "## Analytics Skill\n\n"
        "When answering data questions, follow this skill:\n\n"
        f"{_ANALYTICS_SKILL}"
    )


# Write tools imported here so they're available; gated by ApprovalHook
_write_tools_loaded = False
_write_tools: list[object] = []


def _get_write_tools() -> list[object]:
    global _write_tools_loaded, _write_tools
    if not _write_tools_loaded:
        from app.agent.tools.write_tools import apply_credit, schedule_message, send_message

        _write_tools = [send_message, schedule_message, apply_credit]
        _write_tools_loaded = True
    return _write_tools


def _get_model() -> AnthropicModel:
    api_key = settings.anthropic_api_key
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY must be set in .env or environment variables")

    return AnthropicModel(
        client_args={"api_key": api_key},
        model_id="claude-sonnet-4-20250514",
        max_tokens=4096,
        params={"temperature": 0.3},
    )


def _get_session_manager(session_id: str) -> FileSessionManager:
    storage_path = Path(settings.session_storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    return FileSessionManager(
        session_id=session_id,
        storage_dir=str(storage_path),
    )


def create_agent(session_id: str) -> Agent:
    """Create a fully configured agent for a chat session.

    The agent has:
    - Read tools (auto-execute)
    - Analytics tools (auto-execute)
    - Write tools (gated by ApprovalHook)
    - Session continuity via FileSessionManager
    """
    all_tools = READ_TOOLS + ANALYTICS_TOOLS + _get_write_tools()

    agent = Agent(
        model=_get_model(),
        system_prompt=_build_system_prompt(),
        tools=all_tools,
        hooks=[ApprovalHook()],
        session_manager=_get_session_manager(session_id),
        callback_handler=None,
    )

    logger.info("Created agent for session %s with %d tools", session_id, len(all_tools))
    return agent
