from fastapi import FastAPI

from auth import router as auth_router
from messages import router as messages_router


app = FastAPI(
    title="MessageLock",
    description="A secure messaging API for protecting private communication.",
    version="1.0.0"
)


# Authentication section
app.include_router(auth_router)


# Messaging section
app.include_router(messages_router)


@app.get("/")
def root():
    return {
        "message": "MessageLock API is running"
    }