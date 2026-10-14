from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator

class MessageCreate(BaseModel):
    # The sender is taken from the access token, not the request body.
    recipient_id: int
    content: str = Field(
        min_length=1,
        max_length=2000
    )

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def ensure_utc(cls, value: datetime):
        # SQLite does not store timezones, so restore UTC on read.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
