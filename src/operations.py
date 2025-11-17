"""Database operations (CRUD) for the UserModel using SQLAlchemy."""

import os
from contextlib import contextmanager # ADDED: For cleaner session management
from typing import Any, Optional, Tuple

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from connect_connector import connect_with_connector
from connect_connector_auto_iam_authn import connect_with_connector_auto_iam_authn
from connect_tcp import connect_tcp_socket
from logger import get_logger
from models import Base, UserModel

logger = get_logger("db")

load_dotenv()

ConnectionPoolTuple = Tuple[sqlalchemy.engine.base.Engine, sessionmaker, Optional[Any]]


def init_connection_pool() -> ConnectionPoolTuple:
    """
    Sets up connection pool for the app.
    Returns: (Engine, SessionMaker, Connector | None)
    """
    if os.getenv("DB_HOST"):
        return connect_tcp_socket()

    if os.getenv("INSTANCE_CONNECTION_NAME"):
        # Either a DB_USER or a DB_IAM_USER should be defined. If both are
        # defined, DB_IAM_USER takes precedence.
        return (
            connect_with_connector()
            if os.getenv("DB_PASS")
            else connect_with_connector_auto_iam_authn()
        )

    raise ValueError(
        "Missing database connection type. Please define one of DB_HOST, or INSTANCE_CONNECTION_NAME"
    )


def init_db(engine: sqlalchemy.engine.base.Engine) -> bool:
    """Test database connectivity before serving requests and create tables."""
    try:
        with engine.connect() as conn:
            # check connectivity
            conn.execute(text("SELECT 1;"))
        # create tables if not exists
        Base.metadata.create_all(bind=engine)
        print("database connection success.")
        logger.info("Database connection succeful and tables ensured.")
        return True
    except OperationalError as err:
        logger.error("Database connection failed: %s", err)
        return False


@contextmanager
def get_session(SessionLocal: sessionmaker, commit: bool = False):
    """
    Provides a database session.
    If commit is True, commits on success and rolls back on exception.
    Always closes the session on exit.
    """
    session = SessionLocal()
    try:
        yield session
        if commit:
            session.commit()
    except SQLAlchemyError:
        # Rollback only if a commit was expected and an error occurred
        if commit:
            session.rollback()
        raise
    finally:
        session.close()


def create_user(SessionLocal: sessionmaker, name: str, email: str):
    """Creates a user if not exists, given name and email."""
    try:
        # Use context manager with commit=True for write operation
        with get_session(SessionLocal, commit=True) as session:
            # Check if user exists (to provide clean "already exists" error for Flask route)
            existing = session.query(UserModel).filter_by(email=email).first()
            if existing:
                logger.info("User %s already exists", email)
                return {"error": f"User {email} already exists."}

            user = UserModel(name=name, email=email)
            session.add(user)
            logger.info("User %s created.", email)
            return {"message": f"User {name} added."}
    except SQLAlchemyError as err:
        # Catches exceptions raised and re-raised by get_session (after rollback)
        logger.error("Error in create_user: %s", err)
        return {"error": str(err)}


def read_users(SessionLocal: sessionmaker):
    """Reads all users from the database."""
    try:
        # Use context manager without commit for read operation
        with get_session(SessionLocal) as session:
            users = session.query(UserModel).all()
            return [
                {"id": user.id, "name": user.name, "email": user.email} for user in users
            ]
    except SQLAlchemyError as err:
        logger.error("Error in read_users: %s", err)
        return {"error": str(err)}


def read_user(SessionLocal: sessionmaker, user_id: int):
    """Reads a single user by their ID."""
    try:
        with get_session(SessionLocal) as session:
            user = session.query(UserModel).filter_by(id=user_id).first()
            if user:
                return {"id": user.id, "name": user.name, "email": user.email}

            logger.error("User ID %d not found.", user_id)
            return {"error": "User not found."}
    except SQLAlchemyError as err:
        logger.error("Error in read_user: %s", err)
        return {"error": str(err)}


def update_user(
    SessionLocal: sessionmaker,
    id_to_update: int,
    new_name: str = None,
    new_email: str = None,
):
    """Updates a user's name or email by their ID."""
    try:
        # Use context manager with commit=True for write operation
        with get_session(SessionLocal, commit=True) as session:
            user = session.query(UserModel).filter_by(id=id_to_update).first()
            if not user:
                logger.error("User not found.")
                return {"error": "User not found."}

            if new_name:
                user.name = new_name
            if new_email:
                user.email = new_email

            logger.info("User Updated.")
            return {"message": f"user {id_to_update} updated."}
    except SQLAlchemyError as err:
        logger.error("Error in update_user: %s", err)
        return {"error": str(err)}


def delete_user(SessionLocal: sessionmaker, id_to_delete: int):
    """Deletes a user by their ID."""
    try:
        # Use context manager with commit=True for write operation
        with get_session(SessionLocal, commit=True) as session:
            emp = session.query(UserModel).filter_by(id=id_to_delete).first()
            if not emp:
                logger.error("User not found.")
                return {"error": "User not found."}

            session.delete(emp)
            return {"message": f"User {id_to_delete} deleted."}
    except SQLAlchemyError as err:
        logger.error("Error in delete_user: %s", err)
        return {"error": str(err)}


if __name__ == "__main__":
    engine, session, connector = init_connection_pool()
    try:
        init_db(engine)
        # create_user(session, "test", "test@abc.com")
        # print(create_user(session, "test2", "test2@abc.com"))
        # print(update_user(session, id=1,new_name="test1"))
        print(read_users(session))
        # print(read_user(session, id=1))
    finally:
        if connector:
            connector.close()