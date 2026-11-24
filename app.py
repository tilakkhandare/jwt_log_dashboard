import os
import logging
from logging.handlers import RotatingFileHandler
from collections import deque
from datetime import timedelta
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

app = Flask(__name__)

# Configuration
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-change-in-production")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)

# 1. Configure RotatingFileHandler for size-based log rotation
# Rotates when log reaches 10 KB, keeping up to 3 backup files (app.log.1, app.log.2, app.log.3)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

rotating_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=10 * 1024, backupCount=3, encoding="utf-8"
)
rotating_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(formatter)

logger = logging.getLogger("dashboard_app")
logger.setLevel(logging.INFO)
logger.addHandler(rotating_handler)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

jwt = JWTManager(app)

# Demo users
USERS = {
    "admin": "admin123",
    "viewer": "viewer123",
}


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and return a JWT access token."""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not username or USERS.get(username) != password:
        logger.warning(f"Failed login attempt for user: {username}")
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    logger.info(f"User '{username}' logged in successfully.")
    return jsonify({"access_token": access_token}), 200


@app.route("/activity", methods=["POST"])
@jwt_required()
def generate_activity():
    """Endpoint to generate sample activity logs (useful for testing rotation & dashboard)."""
    current_user = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    count = min(int(data.get("count", 5)), 500)
    message = data.get("message", "Sample user action recorded")

    for i in range(1, count + 1):
        logger.info(f"[User: {current_user}] Event #{i}: {message}")

    return jsonify({
        "status": "success",
        "logged_entries": count,
        "user": current_user,
    }), 201


# 2 & 3. Add a '/logs' route that reads the last N lines, secured with JWT authentication
@app.route("/logs", methods=["GET"])
@jwt_required()
def get_logs():
    """Return the last N lines from the application log file (JWT protected)."""
    current_user = get_jwt_identity()
    try:
        n = int(request.args.get("lines", 20))
        if n <= 0:
            return jsonify({"error": "'lines' parameter must be a positive integer"}), 400
        n = min(n, 1000)  # Cap maximum lines returned
    except ValueError:
        return jsonify({"error": "'lines' parameter must be an integer"}), 400

    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": [], "count": 0}), 200

    # Efficiently read the last N lines using deque
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        recent_lines = [line.rstrip("\n") for line in deque(f, maxlen=n)]

    logger.info(f"User '{current_user}' fetched last {len(recent_lines)} log lines.")
    return jsonify({
        "requested_lines": n,
        "returned_lines": len(recent_lines),
        "log_file": LOG_FILE,
        "logs": recent_lines,
    }), 200


if __name__ == "__main__":
    logger.info("Starting Flask JWT Log Dashboard application...")
    app.run(host="0.0.0.0", port=5000, debug=True)
