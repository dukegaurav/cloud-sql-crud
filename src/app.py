from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from google.cloud.sql.connector import Connector
from sqlmodel import SQLModel

from core.db import engine
from core.logger import get_logger
from routes.userRoutes import router

load_dotenv()

logger = get_logger("app")

connector: Connector | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connector
    # Startup logic
    logger.info("Starting up the application...")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully.")

        # If using Cloud SQL connector, keep reference for shutdown
        if "creator" in str(engine.url):
            connector = Connector()
            logger.debug("Cloud SQL connector initialized.")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield  # Application runs here

    # Shutdown logic
    logger.info("Shutting down the application...")
    try:
        if connector:
            connector.close()
            logger.debug("Cloud SQL connector closed.")
        logger.info("Shutdown completed successfully.")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(title="Cloud SQL Connectivity Test API", lifespan=lifespan)

# Include routes
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
