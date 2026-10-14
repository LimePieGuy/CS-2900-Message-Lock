from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_database
from models import Message, User
from schemas import MessageCreate, MessageResponse

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
        content=message.content
    )

    db.add(new_message)

    try:
        db.commit()
        db.refresh(new_message)
    except Exception:
        db.rollback()
        raise

    return new_message

@router.get("/", response_model=list[MessageResponse])
def get_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """List messages the logged-in user has sent or received."""

    return db.query(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.recipient_id == current_user.id
        )
    ).order_by(Message.created_at, Message.id).all()

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

    return message
