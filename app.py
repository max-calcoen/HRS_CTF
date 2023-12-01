from fileinput import filename
import os
from flask import Flask, current_app, send_from_directory, session, request, jsonify, redirect  # type: ignore
import secrets
import sqlite3
import bcrypt
import redis

app = Flask(__name__, static_url_path="")
app.secret_key = secrets.token_hex()

# connect to redis
redis_client = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


# index.html override
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/signup", methods=["POST"])
def signup():
    global redis_client
    # check if user is already signed in
    if "username" in session:
        return jsonify({"error": "User is already signed in"}), 400
    # filter user input
    if len(request.form["username"]) < 6 or len(request.form["password"]) < 8:
        return jsonify({"error": "Bad username or password"}), 400

    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (request.form["username"],)
    )
    user = cursor.fetchone()
    if user is not None:
        connection.close()
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.hashpw(
        request.form["password"].encode("utf-8"), bcrypt.gensalt()
    )
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (request.form["username"], hashed_password),
    )
    connection.commit()
    connection.close()
    # TODO: sign in with their info and add to session
    session_token = os.urandom(24).hex()
    redis_client.set(session_token, user[0])
    session["token"] = session_token
    # user successfully created account, display home page
    return redirect("/")


@app.route("/signin", methods=["POST"])
def login():
    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (request.form["username"],)
    )
    # check if user exists
    user = cursor.fetchone()
    if user is None:
        # dummy check to equalize response time (prevent timing attack)
        bcrypt.checkpw(
            request.form["password"].encode("utf-8"), "dummy".encode("utf-8")
        )
        connection.close()
        return jsonify({"error": "Incorrect username or password"}), 401

    if bcrypt.checkpw(
        request.form["password"].encode("utf-8"), user[2].encode("utf-8")
    ):
        session["user_id"] = user[0]
        connection.close()
        pass
    connection.close()
    return jsonify({"error": "Incorrect username or password"}), 401


@app.route("/file_request/<path:filename>", methods=["POST"])
def file_request(filename):
    uploads = os.path.join(current_app.root_path, "server_resources")
    file_path = os.path.join(uploads, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(uploads, filename, as_attachment=True)


@app.route("/request_server", methods=["POST"])
def request_server():
    # TODO: start server with port not taken, authenticate the request with session info, set timer to close
    pass


def is_logged_in():
    global redis_client
    session_token = session.get("token")
    # check if token exists and matches session cache
    return session_token is not None and redis_client.get(session_token) is not None


if __name__ == "__main__":
    app.run(port=8080, debug=True)
