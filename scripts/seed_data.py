"""Generate realistic sample data for the property management database.

Run: python -m scripts.seed_data
"""

import asyncio
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

PROPERTIES = [
    {"name": "Sunrise Apartments", "address": "123 Oak Street, Austin, TX 78701"},
    {"name": "Oak Tower Residences", "address": "456 Elm Avenue, Austin, TX 78702"},
    {"name": "Pine Ridge Condos", "address": "789 Pine Boulevard, Austin, TX 78703"},
]

UNITS_PER_PROPERTY = [
    # Sunrise Apartments - 6 units
    [
        {"label": "1A", "bedrooms": 1, "monthly_rent": Decimal("1200.00")},
        {"label": "1B", "bedrooms": 1, "monthly_rent": Decimal("1250.00")},
        {"label": "2A", "bedrooms": 2, "monthly_rent": Decimal("1600.00")},
        {"label": "2B", "bedrooms": 2, "monthly_rent": Decimal("1650.00")},
        {"label": "3A", "bedrooms": 3, "monthly_rent": Decimal("2100.00")},
        {"label": "3B", "bedrooms": 3, "monthly_rent": Decimal("2200.00")},
    ],
    # Oak Tower - 5 units
    [
        {"label": "101", "bedrooms": 1, "monthly_rent": Decimal("1100.00")},
        {"label": "102", "bedrooms": 1, "monthly_rent": Decimal("1150.00")},
        {"label": "201", "bedrooms": 2, "monthly_rent": Decimal("1500.00")},
        {"label": "202", "bedrooms": 2, "monthly_rent": Decimal("1550.00")},
        {"label": "301", "bedrooms": 3, "monthly_rent": Decimal("1950.00")},
    ],
    # Pine Ridge - 4 units
    [
        {"label": "A1", "bedrooms": 2, "monthly_rent": Decimal("1800.00")},
        {"label": "A2", "bedrooms": 2, "monthly_rent": Decimal("1850.00")},
        {"label": "B1", "bedrooms": 3, "monthly_rent": Decimal("2300.00")},
        {"label": "B2", "bedrooms": 3, "monthly_rent": Decimal("2400.00")},
    ],
]

TENANTS = [
    {"name": "John Martinez", "email": "john.martinez@email.com", "phone": "(512) 555-0101"},
    {"name": "Sarah Chen", "email": "sarah.chen@email.com", "phone": "(512) 555-0102"},
    {"name": "Michael Thompson", "email": "michael.t@email.com", "phone": "(512) 555-0103"},
    {"name": "Emily Rodriguez", "email": "emily.r@email.com", "phone": "(512) 555-0104"},
    {"name": "David Kim", "email": "david.kim@email.com", "phone": "(512) 555-0105"},
    {"name": "Lisa Patel", "email": "lisa.patel@email.com", "phone": "(512) 555-0106"},
    {"name": "James Wilson", "email": "james.wilson@email.com", "phone": "(512) 555-0107"},
    {"name": "Amanda Foster", "email": "amanda.foster@email.com", "phone": "(512) 555-0108"},
    {"name": "Robert Chang", "email": "robert.chang@email.com", "phone": "(512) 555-0109"},
    {"name": "Jessica Nguyen", "email": "jessica.n@email.com", "phone": "(512) 555-0110"},
    {"name": "Chris Davis", "email": "chris.davis@email.com", "phone": "(512) 555-0111"},
    {"name": "Maria Gonzalez", "email": "maria.g@email.com", "phone": "(512) 555-0112"},
]

PAYMENT_METHODS = ["ach", "check", "credit_card", "cash"]


async def seed(session: AsyncSession) -> None:
    """Insert all sample data."""

    # Clear existing data in reverse FK order
    for table in [
        "action_log", "chat_message", "chat_session",
        "scheduled_message", "message", "payment", "charge",
        "lease", "tenant", "unit", "property",
    ]:
        await session.execute(text(f"DELETE FROM {table}"))

    # -- Properties --
    prop_ids: list[int] = []
    for prop in PROPERTIES:
        result = await session.execute(
            text("INSERT INTO property (name, address) VALUES (:name, :address) RETURNING id"),
            prop,
        )
        prop_ids.append(result.scalar_one())

    # -- Units --
    unit_ids: list[int] = []
    unit_rents: list[Decimal] = []
    for prop_idx, units in enumerate(UNITS_PER_PROPERTY):
        for unit in units:
            result = await session.execute(
                text(
                    "INSERT INTO unit (property_id, label, bedrooms, monthly_rent, status) "
                    "VALUES (:pid, :label, :bedrooms, :rent, :status) RETURNING id"
                ),
                {
                    "pid": prop_ids[prop_idx],
                    "label": unit["label"],
                    "bedrooms": unit["bedrooms"],
                    "rent": unit["monthly_rent"],
                    "status": "leased",
                },
            )
            uid = result.scalar_one()
            unit_ids.append(uid)
            unit_rents.append(unit["monthly_rent"])

    # Mark 3 units as available (no tenant)
    available_indices = [1, 8, 13]  # 1B at Sunrise, 201 at Oak Tower, B2 at Pine Ridge
    for idx in available_indices:
        await session.execute(
            text("UPDATE unit SET status = 'available' WHERE id = :id"),
            {"id": unit_ids[idx]},
        )

    # -- Tenants --
    tenant_ids: list[int] = []
    for tenant in TENANTS:
        result = await session.execute(
            text("INSERT INTO tenant (name, email, phone) VALUES (:name, :email, :phone) RETURNING id"),
            tenant,
        )
        tenant_ids.append(result.scalar_one())

    # -- Leases (active leases for occupied units) --
    lease_data: list[dict[str, object]] = []
    tenant_cursor = 0
    today = date.today()
    for i, uid in enumerate(unit_ids):
        if i in available_indices:
            continue
        if tenant_cursor >= len(tenant_ids):
            break
        start = today - timedelta(days=random.randint(90, 365))
        end = start + timedelta(days=365)
        status = "active" if end >= today else "ended"
        lease_row = {
            "unit_id": uid,
            "tenant_id": tenant_ids[tenant_cursor],
            "rent_amount": unit_rents[i],
            "start_date": start,
            "end_date": end,
            "status": status,
        }
        result = await session.execute(
            text(
                "INSERT INTO lease (unit_id, tenant_id, rent_amount, start_date, end_date, status) "
                "VALUES (:unit_id, :tenant_id, :rent_amount, :start_date, :end_date, :status) RETURNING id"
            ),
            lease_row,
        )
        lease_id = result.scalar_one()
        lease_data.append({**lease_row, "id": lease_id, "tenant_idx": tenant_cursor})
        tenant_cursor += 1

    # -- Charges & Payments (last 3 months) --
    for lease in lease_data:
        lid = lease["id"]
        rent = lease["rent_amount"]
        assert isinstance(lid, int)
        assert isinstance(rent, Decimal)

        for month_offset in range(3):
            period = today.replace(day=1) - timedelta(days=30 * month_offset)
            period_str = period.strftime("%Y-%m")
            due = period.replace(day=1)
            roll = random.random()

            if month_offset == 0:
                # Current month: mix of open, paid, overdue
                if roll < 0.4:
                    status, paid = "open", Decimal("0.00")
                elif roll < 0.7:
                    status, paid = "paid", rent
                else:
                    status, paid = "overdue", Decimal("0.00")
            elif month_offset == 1:
                # Last month: mostly paid, some overdue
                if roll < 0.75:
                    status, paid = "paid", rent
                else:
                    status, paid = "overdue", Decimal("0.00")
            else:
                # 2 months ago: almost all paid
                if roll < 0.9:
                    status, paid = "paid", rent
                else:
                    status, paid = "overdue", Decimal("0.00")

            result = await session.execute(
                text(
                    "INSERT INTO charge (lease_id, period_month, amount_due, amount_paid, due_date, status, kind) "
                    "VALUES (:lid, :period, :due_amt, :paid_amt, :due_date, :status, 'rent') RETURNING id"
                ),
                {
                    "lid": lid,
                    "period": period_str,
                    "due_amt": rent,
                    "paid_amt": paid,
                    "due_date": due,
                    "status": status,
                },
            )
            charge_id = result.scalar_one()

            if status == "paid":
                pay_date = due + timedelta(days=random.randint(0, 5))
                await session.execute(
                    text(
                        "INSERT INTO payment (charge_id, amount, paid_at, method) "
                        "VALUES (:cid, :amt, :paid_at, :method)"
                    ),
                    {
                        "cid": charge_id,
                        "amt": rent,
                        "paid_at": datetime(pay_date.year, pay_date.month, pay_date.day, tzinfo=timezone.utc),
                        "method": random.choice(PAYMENT_METHODS),
                    },
                )

            # Late fees on overdue charges
            if status == "overdue" and month_offset > 0:
                await session.execute(
                    text(
                        "INSERT INTO charge (lease_id, period_month, amount_due, amount_paid, due_date, status, kind) "
                        "VALUES (:lid, :period, :fee, 0.00, :due_date, 'open', 'late_fee')"
                    ),
                    {
                        "lid": lid,
                        "period": period_str,
                        "fee": Decimal("75.00"),
                        "due_date": due + timedelta(days=15),
                    },
                )

    # -- Messages (some past outbound messages) --
    for i in range(5):
        tid = tenant_ids[i]
        await session.execute(
            text(
                "INSERT INTO message (tenant_id, body, direction, status) "
                "VALUES (:tid, :body, 'outbound', 'sent')"
            ),
            {
                "tid": tid,
                "body": f"Hi {TENANTS[i]['name'].split()[0]}, this is a reminder that your rent is due on the 1st. Please let us know if you have any questions.",
            },
        )

    await session.commit()
    print("Seed data inserted successfully.")
    print(f"  Properties: {len(PROPERTIES)}")
    print(f"  Units: {len(unit_ids)} ({len(unit_ids) - len(available_indices)} leased, {len(available_indices)} available)")
    print(f"  Tenants: {len(tenant_ids)}")
    print(f"  Leases: {len(lease_data)}")


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
