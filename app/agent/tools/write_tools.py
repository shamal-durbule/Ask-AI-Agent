"""Write tools that require human approval before execution.

These tools are intercepted by ApprovalHook, which raises an interrupt
before they run. The hook handles the approval flow; these tools just
execute the actual data changes.

Delivery of messages is mocked -- the point is the approval flow.
"""

import json
import logging
from datetime import datetime, timezone

from strands import tool

from app.database import async_session_factory
from app.repositories.charge_repo import ChargeRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.tenant_repo import TenantRepository

logger = logging.getLogger(__name__)


@tool
async def send_message(tenant_id: int, body: str) -> str:
    """Send a message to a tenant.

    Args:
        tenant_id: The ID of the tenant to message.
        body: The message content to send.

    This action requires approval. The manager will see a preview before
    the message is sent. Message delivery is mocked (no real SMS/email).
    """
    async with async_session_factory() as session:
        tenant_repo = TenantRepository(session)
        tenant = await tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            return f"Error: Tenant #{tenant_id} not found."

        msg_repo = MessageRepository(session)
        message = await msg_repo.create_outbound(tenant_id=tenant_id, body=body)
        await session.commit()

        logger.info("Message sent to %s (tenant #%d): %s", tenant.name, tenant_id, body[:100])
        return json.dumps({
            "status": "sent",
            "message_id": message.id,
            "tenant": tenant.name,
            "body": body,
            "note": "Delivery mocked -- message recorded in database.",
        })


@tool
async def schedule_message(tenant_id: int, body: str, send_at: str) -> str:
    """Schedule a message to be sent to a tenant at a future time.

    Args:
        tenant_id: The ID of the tenant to message.
        body: The message content to send.
        send_at: When to send the message (ISO 8601 datetime string).

    This action requires approval. The manager will see a preview before
    the message is scheduled. Actual delivery at the scheduled time is mocked.
    """
    try:
        scheduled_time = datetime.fromisoformat(send_at)
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
    except ValueError:
        return f"Error: Invalid datetime format '{send_at}'. Use ISO 8601 format."

    if scheduled_time <= datetime.now(timezone.utc):
        return "Error: Scheduled time must be in the future."

    async with async_session_factory() as session:
        tenant_repo = TenantRepository(session)
        tenant = await tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            return f"Error: Tenant #{tenant_id} not found."

        msg_repo = MessageRepository(session)
        scheduled = await msg_repo.create_scheduled(
            tenant_id=tenant_id,
            body=body,
            send_at=scheduled_time,
            tenant_name=tenant.name,
        )
        await session.commit()

        logger.info(
            "Message scheduled for %s to %s (tenant #%d)",
            send_at, tenant.name, tenant_id,
        )
        return json.dumps({
            "status": "scheduled",
            "scheduled_message_id": scheduled.id,
            "tenant": tenant.name,
            "send_at": send_at,
            "body": body,
            "note": "Delivery at scheduled time is mocked.",
        })


@tool
async def apply_credit(lease_id: int, amount: float, reason: str) -> str:
    """Apply a credit or waive a late fee on a lease.

    Args:
        lease_id: The lease ID to apply the credit to.
        amount: The credit amount in dollars (positive number, will be applied as negative charge).
        reason: The reason for the credit (e.g., 'late fee waiver', 'maintenance inconvenience').

    This action requires approval. The manager will see a preview of the
    credit before it is applied.
    """
    if amount <= 0:
        return "Error: Credit amount must be a positive number."

    from decimal import Decimal

    async with async_session_factory() as session:
        charge_repo = ChargeRepository(session)
        credit = await charge_repo.create_credit(
            lease_id=lease_id,
            amount=Decimal(str(amount)),
            reason=reason,
        )
        await session.commit()

        logger.info(
            "Credit of $%.2f applied to lease #%d (reason: %s)",
            amount, lease_id, reason,
        )
        return json.dumps({
            "status": "applied",
            "charge_id": credit.id,
            "lease_id": lease_id,
            "amount": f"-${amount:.2f}",
            "reason": reason,
            "kind": "credit",
        })
