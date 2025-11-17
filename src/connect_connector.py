"""Connection logic for connecting to Cloud SQL using the Cloud SQL Python Connector (password authentication)."""

import os

import pg8000
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def connect_with_connector() -> (
    tuple[sqlalchemy.engine.base.Engine, sessionmaker, Connector]
):
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres using the Connector.

    Returns:
        A tuple containing the SQLAlchemy Engine, SessionMaker, and the Connector object.
    """
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")  # e.g. 'my-db-user'
    db_pass = os.getenv("DB_PASS")  # e.g. 'my-db-password' # Renamed db_p
    db_name = os.getenv("DB_NAME")  # e.g. 'my-database'

    ip_type = IPTypes.PRIVATE

    # initialize Cloud SQL Python Connector object
    connector = Connector(refresh_strategy="LAZY")

    def getconn() -> pg8000.dbapi.Connection:
        """Helper function to create a new pg8000 connection."""
        conn: pg8000.dbapi.Connection = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=ip_type,
        )
        return conn

    # The Cloud SQL Python Connector can be used with SQLAlchemy
    # using the 'creator' argument to 'create_engine'
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        # Pool size is the maximum number of permanent connections to keep.
        pool_size=5,
        # Temporarily exceeds the set pool_size if no connections are available.
        max_overflow=2,
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        pool_timeout=30,  # 30 seconds
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # re-established
        pool_recycle=1800,  # 30 minutes
        echo=False,
        future=True,
    )
    return engine, sessionmaker(bind=engine), connector
