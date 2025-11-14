import datetime
import os

from quart import Quart, jsonify, request

app = Quart(__name__)


# init_db lazily instantiates a database connection pool. Users of Cloud Run or
# App Engine may wish to skip this lazy instantiation and connect as soon
# as the function is loaded. This is primarily to help testing.
@app.before_request
def init_db() -> sqlalchemy.engine.base.Engine:
    """Initiates connection to database and its structure."""
    global db
    if db is None:
        db = init_connection_pool()
        migrate_db(db)


@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user with name and email"""
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            return jsonify({"error": "Name and email are required"}), 400

    except (KeyError, TypeError, ValueError) as e:
        logger.error("Error in create_user: %s", e)
        return jsonify({"error": "Interal server error"}), 500
