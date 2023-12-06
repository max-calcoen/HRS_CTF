import os
from flask import Flask, current_app, send_from_directory, session, request, jsonify, redirect, render_template  # type: ignore
import secrets
import sqlite3
import bcrypt
import redis
from subprocess import Popen
import threading
import time

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
        session_token = os.urandom(24).hex()
        redis_client.set(session_token, user[0])
        session["token"] = session_token
        connection.close()
        return jsonify({"success": "Login successful"}), 200
    connection.close()
    return jsonify({"error": "Incorrect username or password"}), 401


@app.route("/file_request/<path:filename>", methods=["GET"])
def file_request(filename):
    uploads = os.path.join(current_app.root_path, "server_resources")
    file_path = os.path.join(uploads, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(uploads, filename, as_attachment=True)


@app.route("/request_server", methods=["POST"])
def request_server():
    exercise = request.json["exercise"]

    # filter user input
    try:
        exercise = int(exercise)
    except:
        return jsonify({"error": "Invalid exercise id"}), 400

    # get path
    path = os.listdir("gym_resources")[exercise - 1]

    def target():
        try:
            process = Popen(["python", f"gym_resources/{path}/app.py"])
            process.wait(600)  # 10 mins
            if process.poll() is None:
                process.terminate()
        except:
            return jsonify({"error": "Bad exercise request"}), 400

    thread = threading.Thread(target=target)
    thread.start()
    return jsonify({"success": "Server started"}), 200


# if logged in, return id, otherwise false
def is_logged_in():
    global redis_client
    session_token = session.get("token")
    # check if token exists and matches session cache
    return (
        redis_client.get(session_token)
        if session_token is not None and redis_client.get(session_token) is not None
        else False
    )


@app.route("/gym")
def get_gym():
    # get gym data
    if not is_logged_in():
        return render_template("gym.html", [])
    connection = sqlite3.connect("users.sqlite")
    cur = connection.cursor()
    cur.execute(
        "SELECT completedproblems FROM users WHERE id = ?",
        (redis_client.get(session.get("token"))),
    )
    probs = cur.fetchone()
    connection.close()
    probs = [int(prob) for prob in probs[0].split(",")]
    print(probs)
    return render_template("gym.html", probs)


@app.route("/probdone", methods=["POST"])
def probdone():
    prob_id = request.form["prob_id"]
    if not is_logged_in():
        return jsonify({"error": "Not logged in"}), 401

    # filter user input
    try:
        prob_id = int(prob_id)
    except:
        return jsonify({"error": "Invalid problem id"}), 400
    connection = sqlite3.connect("users.sqlite")
    cur = connection.cursor()
    cur.execute(
        "SELECT completedproblems FROM users WHERE id = ?",
        (redis_client.get(session.get("token"))),
    )
    probs = cur.fetchone()[0].strip("[]").split(", ")
    try:
        probs = [int(prob) for prob in probs]
    except:
        probs = []
    probs.append(int(prob_id))
    connection.executescript(
        f"UPDATE users SET completedproblems = '{str(probs)}' WHERE id={redis_client.get(session.get('token'))}"
    )
    # TODO: add points
    connection.commit()
    connection.close()
    return ""


if __name__ == "__main__":
    app.run(port=8080, debug=True)
