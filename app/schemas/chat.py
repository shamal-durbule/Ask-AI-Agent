from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class ApprovalRequest(BaseModel):
    interrupt_id: str
    decision: str = Field(..., pattern="^(approve|reject|edit)$")
    edited_params: dict[str, object] | None = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    metadata_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
