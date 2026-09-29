from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from schemas import MessageCreate, MessageResponse


router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)


# Temporary storage until the database section is completed.
messages = []


@router.post("/", response_model=MessageResponse)
def send_message(message: MessageCreate):
    new_message = MessageResponse(
        id=len(messages) + 1,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        content=message.content,
        created_at=datetime.now(timezone.utc)
    )

    messages.append(new_message)

    return new_message


@router.get("/", response_model=list[MessageResponse])
def get_messages():
    return messages


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(message_id: int):
    for message in messages:
        if message.id == message_id:
            return message

    raise HTTPException(
        status_code=404,
        detail="Message not found"
    )