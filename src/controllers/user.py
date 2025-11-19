from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from core.logger import get_logger
from models.user import User

logger = get_logger("controller")


def create_user(session, user: User):
    try:
        # Check if email already exists
        existing_user = session.exec(
            select(User).where(User.email == user.email)
        ).first()
        if existing_user:
            logger.warning(f"Email already exists: {user.email}")
            return None

        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error creating user: {e}")
        session.rollback()
        raise


def get_users(session):
    return session.exec(select(User)).all()


def get_user(session, user_id: int):
    return session.get(User, user_id)


def update_user(session, user_id: int, data: dict):
    user = session.get(User, user_id)
    if not user:
        return None
    for key, value in data.items():
        setattr(user, key, value)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session, user_id: int):
    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()
        return True
    return False
