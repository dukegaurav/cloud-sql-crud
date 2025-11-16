import os

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker


def connect_tcp_socket() -> tuple[sqlalchemy.engine.base.Engine,sessionmaker, None]:
    """Initializes a TCP connection pool for a Cloud SQL instance of Postgres."""
    db_host = os.getenv("DB_HOST")  # e.g. '127.0.0.1'
    db_user = os.getenv("DB_USER")  # e.g. 'my-db-user'
    db_p = os.getenv("DB_PASS")  # e.g. 'my-db-password'
    db_name = os.getenv("DB_NAME", "postgres")  # e.g. 'my-database'
    db_port = os.getenv("DB_PORT", "5432")  # e.g. 5432


    engine = create_engine(
        sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=db_user,
            password=db_p,
            host=db_host,
            port=db_port,
            database=db_name,
        ),
        # Pool size is the maximum number of permanent connections to keep.
        pool_size=5,
        # Temporarily exceeds the set pool_size if no connections are available.
        max_overflow=2,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # SQLAlchemy automatically uses delays between failed connection attempts,
        # but provides no arguments for configuration.
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        pool_timeout=30,  # 30 seconds
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # re-established
        pool_recycle=1800,  # 30 minutes
    )
    return engine, sessionmaker(bind=engine), None
