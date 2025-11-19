from google.cloud.sql.connector import Connector, IPTypes
from sqlmodel import Session, create_engine

from .config import Settings
from .logger import get_logger

settings = Settings()
logger = get_logger("db")


def get_engine():
    try:
        if settings.DB_HOST:
            # Native authentication using DB_HOST
            logger.debug("Using DB_HOST for connection.")
            url = f"postgresql+pg8000://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}/{settings.DB_NAME}"
            return create_engine(url, echo=True)

        elif settings.INSTANCE_CONNECTION_NAME:
            connector = Connector()
            if settings.DB_PASS:
                logger.debug("Using SQL connector with password authentication.")

                def getconn():
                    return connector.connect(
                        settings.INSTANCE_CONNECTION_NAME,
                        "pg8000",
                        user=settings.DB_USER,
                        password=settings.DB_PASS,
                        db=settings.DB_NAME,
                        ip_type=IPTypes.PRIVATE,
                    )

            else:
                logger.debug("Using IAM authentication for Cloud SQL.")

                def getconn():
                    return connector.connect(
                        settings.INSTANCE_CONNECTION_NAME,
                        "pg8000",
                        user=settings.DB_USER,
                        enable_iam_auth=True,
                        db=settings.DB_NAME,
                        ip_type=IPTypes.PRIVATE,
                    )

            return create_engine(
                "postgresql+pg8000://", creator=getconn
            )  # , echo=True)

        else:
            raise ValueError("No valid DB connection configuration found.")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


engine = get_engine()


def get_session():
    with Session(engine) as session:
        yield session
