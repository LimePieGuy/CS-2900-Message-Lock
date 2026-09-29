from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    sender_id: int
    recipient_id: int
    content: str = Field(
        min_length=1,
        max_length=2000
    )


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime