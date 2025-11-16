import os
from typing import Optional, Any
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from connect_connector import connect_with_connector
from connect_connector_auto_iam_authn import connect_with_connector_auto_iam_authn
from connect_tcp import connect_tcp_socket
from logger import get_logger

from models import Base, UserModel

logger = get_logger("db")

load_dotenv()

def init_connection_pool() -> tuple[sqlalchemy.engine.base.Engine, sessionmaker, Optional[Any]]:
    """
    Sets up connection pool for the app.
    Returns: (Engine, SessionMaker, Connector | None)
    """
    # use a TCP socket when DB_HOST (e.g. 127.0.0.1) is defined
    if os.getenv("DB_HOST"):
        return connect_tcp_socket()

    # use the connector when INSTANCE_CONNECTION_NAME (e.g. project:region:instance) is defined
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

def init_db(engine) -> bool:
    """Test database connectivity before serving requests."""
    try:
        with engine.connect() as conn:
            # check connectivity
            conn.execute(text("SELECT 1;"))
        # create tables if not exists
        Base.metadata.create_all(bind=engine)
        print("database connection success.")
        logger.info("Database connection succeful and tables ensured.")
        return True
    except OperationalError as e:
        logger.error("Database connection failed: %s",e)
        return False

def create_user(SessionLocal: sessionmaker, name: str, email: str):
    """Creatd a user if not exists, given name and email."""
    try:
        # Check if user exists
        session = SessionLocal()
        existing = session.query(UserModel).filter_by(email=email).first()
        if existing:
            logger.info("User %s already exists", email)
            return {"error": f"User {email} already exists."}
        user = UserModel(name=name, email=email)
        session.add(user)
        session.commit()
        logger.info("User %s created.", email)
        return {"message": f"User {name} added."}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Error in create_user: %s", e)
        return {"error": str(e)}
    finally:
        session.close()
        logger.info("Session Closed")


def read_users(SessionLocal: sessionmaker):
    session = SessionLocal()
    try:
        users = session.query(UserModel).all()
        return [{"id": user.id, "name": user.name, "email": user.email} for user in users]
    except SQLAlchemyError as e:
        logger.error("Error in read_users: %s", e)
        return {"error": str(e)}
    finally:
        session.close()

def read_user(SessionLocal: sessionmaker, user_id: int):
    """Reads a single user by their ID."""
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter_by(id=user_id).first()
        if user:
            return {"id": user.id, "name": user.name, "email": user.email}
        else:
            logger.error("User ID %d not found.", user_id)
            return {"error": "User not found."}
    except SQLAlchemyError as e:
        logger.error("Error in read_user: %s", e)
        return {"error": str(e)}
    finally:
        session.close()

def update_user(SessionLocal:sessionmaker, id: int, new_name: str = None, new_email: str = None):
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter_by(id=id).first()
        if not user:
            logger.error("User not found.")
            return {"error": "User not found."}
        if new_name:
            user.name = new_name
        if new_email:
            user.email = new_email
        session.commit()
        logger.info("User Updated.")
        return {"message": f"user {id} updated."}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Error in update_user: %s", e)
        return {"error": str(e)}
    finally:
        session.close()

def delete_user(SessionLocal:sessionmaker, id: int):
    session = SessionLocal()
    try:
        emp = session.query(UserModel).filter_by(id=id).first()
        if not emp:
            logger.error("User not found.")
            return {"error": "User not found."}
        session.delete(emp)
        session.commit()
        return {"message": f"User {id} deleted."}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Error in delete_user: %s", e)
        return {"error": str(e)}
    finally:
        session.close()



# if __name__ == "__main__":
#     engine, session, connector = init_connection_pool()
#     try:
#         init_db(engine)
#         print(create_user(session, "test", "test@abc.com"))
#         print(update_user(session, id=1,new_name="test1"))
#         print(read_users(session))
#     finally:
#         if connector:
#             connector.close()
#             logger.info("Cloud SQL Connector closed.")