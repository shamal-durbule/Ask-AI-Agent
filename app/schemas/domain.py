from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class UnitResponse(BaseModel):
    id: int
    label: str
    bedrooms: int
    monthly_rent: Decimal
    status: str

    model_config = {"from_attributes": True}


class PropertyResponse(BaseModel):
    id: int
    name: str
    address: str
    units: list[UnitResponse] = []
    total_units: int = 0
    occupied_units: int = 0

    model_config = {"from_attributes": True}


class LeaseResponse(BaseModel):
    id: int
    unit_label: str
    property_name: str
    tenant_name: str
    rent_amount: Decimal
    start_date: date
    end_date: date
    status: str


class TenantResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    active_lease: LeaseResponse | None = None

    model_config = {"from_attributes": True}


class ChargeResponse(BaseModel):
    id: int
    lease_id: int
    period_month: str
    amount_due: Decimal
    amount_paid: Decimal
    due_date: date
    status: str
    kind: str
    tenant_name: str | None = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    tenant_id: int
    body: str
    direction: str
    status: str
    sent_at: datetime

    model_config = {"from_attributes": True}
