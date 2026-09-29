from fastapi import APIRouter


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register():
    # TODO: Implement user registration.
    return {
        "message": "Registration endpoint not implemented yet"
    }


@router.post("/login")
def login():
    # TODO: Implement user authentication.
    return {
        "message": "Login endpoint not implemented yet"
    }