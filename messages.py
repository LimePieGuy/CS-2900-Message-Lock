from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_database
from models import Message, User
from schemas import MessageCreate, MessageResponse
from crypto import encrypt_message, decrypt_message

router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)

@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Send a message from the logged-in user to another user."""

    recipient = db.get(User, message.recipient_id)

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found"
        )

    new_message = Message(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=encrypt_message(
            message.content,
            current_user.id,
            recipient.id
        )
    )

    db.add(new_message)

    try:
        db.commit()
        db.refresh(new_message)
    except Exception:
        db.rollback()
        raise

    return decrypted_response(new_message)


def decrypted_response(message: Message) -> MessageResponse:
    """Decrypt content for the response without changing the database."""
    try:
        plaintext = decrypt_message(
            message.content,
            message.sender_id,
            message.recipient_id
        )
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Message could not be verified or decrypted."
        ) from None

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        content=plaintext,
        created_at=message.created_at
    )

@router.get("/", response_model=list[MessageResponse])
def get_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """List messages the logged-in user has sent or received."""

    messages = db.query(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id
        )
    ).order_by(Message.created_at, Message.id).all()

    return [decrypted_response(message) for message in messages]

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Get one message, if the logged-in user sent or received it."""

    message = db.get(Message, message_id)

    # Return 404 for other users' messages so their IDs are not revealed.
    if message is None or current_user.id not in (
        message.sender_id,
        message.recipient_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    return decrypted_response(message)
