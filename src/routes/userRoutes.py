from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from controllers.user import create_user, delete_user, get_user, get_users, update_user
from core.db import get_session
from models.user import User

router = APIRouter()


@router.post("/users", response_model=User)
def create(user: User, session: Session = Depends(get_session)):
    new_user = create_user(session, user)
    if new_user is None:
        raise HTTPException(status_code=400, detail="Email already exists")
    return new_user


@router.get("/users", response_model=list[User])
def read_all(session: Session = Depends(get_session)):
    return get_users(session)


@router.get("/users/{user_id}", response_model=User)
def read(user_id: int, session: Session = Depends(get_session)):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=User)
def update(user_id: int, data: dict, session: Session = Depends(get_session)):
    user = update_user(session, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{user_id}")
def delete(user_id: int, session: Session = Depends(get_session)):
    if not delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}
