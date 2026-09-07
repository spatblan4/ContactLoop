from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import UnauthorizedError
from app.dao import AuthTokenDAO, UserDAO
from app.schemas.auth import AuthLogin, AuthRegister, AuthResponse, AuthUser

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_response(user, db: Session) -> AuthResponse:
    token = AuthTokenDAO(db).issue(user.id, actor_id=user.id)
    return AuthResponse(user=AuthUser.model_validate(user), token=token)


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: AuthRegister, db: Session = Depends(get_db)):
    user = UserDAO(db).register(payload.email, payload.password, payload.name)
    response = _issue_response(user, db)
    db.commit()
    return response


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    user = UserDAO(db).verify(payload.email, payload.password)
    if user is None:
        raise UnauthorizedError("invalid email or password")
    response = _issue_response(user, db)
    db.commit()
    return response


@router.get("/me", response_model=AuthUser)
def me(user=Depends(get_current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() == "bearer":
        AuthTokenDAO(db).revoke(token)
    db.commit()
    return None
