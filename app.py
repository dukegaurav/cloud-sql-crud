"""Flask application for a Cloud SQL CRUD service."""

import os
import sys
from typing import Any, Optional

from flask import Flask, jsonify, request
from sqlalchemy.orm import sessionmaker

from logger import get_logger

# Import functions from other files
from operations import (
    create_user,
    delete_user,
    init_connection_pool,
    init_db,
    read_user,
    read_users,
    update_user,
)

# --- FLASK SETUP ---
app = Flask(__name__)
logger = get_logger("app")

# Global variables for application lifecycle management
# pylint: disable=invalid-name
DB_SESSION_LOCAL: Optional[sessionmaker] = None
DB_CONNECTOR: Optional[Any] = None
# pylint: enable=invalid-name


def initialize_database():
    """Initializes the database connection pool and creates tables once."""
    # pylint: disable=global-statement
    global DB_SESSION_LOCAL, DB_CONNECTOR
    # pylint: enable=global-statement

    if DB_SESSION_LOCAL is None:
        try:
            # init_connection_pool must return (engine, sessionmaker, connector | None)
            engine, session_local, connector = init_connection_pool()
            init_db(engine)  # Create tables if they don't exist

            DB_SESSION_LOCAL = session_local
            DB_CONNECTOR = connector
            logger.info("Database connection pool and tables initialized.")
        except Exception as err:
            # pylint: disable=broad-except
            logger.error("Failed to initialize database: %s", err)
            # Exit the process if connection fails at startup
            sys.exit(1)
            # pylint: enable=broad-except


# --- FIX: Call initialization immediately upon module import ---
# This ensures the database is connected and DB_SESSION_LOCAL is set
# when a WSGI server (like Gunicorn) loads the application.
initialize_database()


def get_session_local() -> sessionmaker:
    """Returns the initialized SQLAlchemy sessionmaker, raising an error if uninitialized."""
    if DB_SESSION_LOCAL is None:
        # This code should now only be reachable if initialization failed (and exited)
        # or if there is a severe race condition.
        logger.critical("Database session factory is not initialized.")
        raise RuntimeError("Database connection not initialized.")
    return DB_SESSION_LOCAL


# --- CRUD ROUTES ---


@app.route("/users", methods=["POST"])
def create_user_route():
    """Creates a new user with name and email."""
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            return jsonify({"error": "Name and email are required"}), 400

        session_local = get_session_local()
        result = create_user(session_local, name, email)

        if "error" in result:
            status = 409 if "already exists" in result.get("error", "") else 500
            return jsonify(result), status

        return jsonify(result), 201  # 201 Created

    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Error in create_user_route: %s", err)
        return jsonify({"error": "Internal server error"}), 500
        # pylint: enable=broad-except


@app.route("/users", methods=["GET"])
def read_all_users_route():
    """Reads all users."""
    try:
        session_local = get_session_local()
        users = read_users(session_local)

        if isinstance(users, dict) and "error" in users:
            return jsonify(users), 500

        return jsonify(users), 200
    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Error in read_all_users_route: %s", err)
        return jsonify({"error": "Internal server error"}), 500
        # pylint: enable=broad-except


@app.route("/users/<int:user_id>", methods=["GET"])
def read_single_user_route(user_id: int):
    """Reads a single user by ID."""
    try:
        session_local = get_session_local()
        # Call the synchronous CRUD function
        user = read_user(session_local, user_id)

        if "error" in user:
            if user["error"] == "User not found.":
                return jsonify(user), 404  # 404 Not Found
            return jsonify(user), 500

        return jsonify(user), 200
    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Error in read_single_user_route: %s", err)
        return jsonify({"error": "Internal server error"}), 500
        # pylint: enable=broad-except


@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user_route(user_id: int):
    """Updates a user's name or email by ID."""
    try:
        data = request.get_json()
        new_name = data.get("name")
        new_email = data.get("email")

        if not new_name and not new_email:
            return (
                jsonify(
                    {"error": "Either 'name' or 'email' must be provided for update"}
                ),
                400,
            )

        session_local = get_session_local()
        result = update_user(session_local, user_id, new_name, new_email)

        if "error" in result:
            if result["error"] == "User not found.":
                return jsonify(result), 404
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Error in update_user_route: %s", err)
        return jsonify({"error": "Internal server error"}), 500
        # pylint: enable=broad-except


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user_route(user_id: int):
    """Deletes a user by ID."""
    try:
        session_local = get_session_local()
        result = delete_user(session_local, user_id)

        if "error" in result:
            if result["error"] == "User not found.":
                return jsonify(result), 404
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Error in delete_user_route: %s", err)
        return jsonify({"error": "Internal server error"}), 500
        # pylint: enable=broad-except


if __name__ == "__main__":
    # This block is only for local execution via 'python app.py'

    # Run the Flask app
    try:
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    except Exception as err:
        # pylint: disable=broad-except
        logger.error("Application failed to run: %s", err)
        # pylint: enable=broad-except
    finally:
        # Close the global Cloud SQL Connector when the application stops locally
        if DB_CONNECTOR:
            DB_CONNECTOR.close()
            logger.info("Cloud SQL Connector closed during shutdown.")
