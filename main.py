from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_tables
from auth import router as auth_router
from messages import router as messages_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(
    title="MessageLock",
    description="A secure messaging API for protecting private communication.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(messages_router)

@app.get("/")
def root():
    return {
        "message": "MessageLock API is running"
    }
