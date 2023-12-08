import os
from flask import Flask, current_app, send_from_directory, session, request, jsonify, redirect, render_template  # type: ignore
import secrets
import sqlite3
import bcrypt
import redis
from subprocess import Popen
import threading
import json

app = Flask(__name__, static_url_path="")
app.secret_key = secrets.token_hex()

# connect to redis
redis_client = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


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


# index.html override
@app.route("/")
def home():
    # get username from session cache
    if not is_logged_in():
        return render_template("index.html")
    user_id = redis_client.get(session.get("token"))
    # get username from database
    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    username = cursor.fetchone()[0]
    connection.close()
    return render_template("index.html", username=username)


@app.route("/signin")
def signin():
    if is_logged_in():
        return redirect("/")
    return send_from_directory("static", "signin.html")


@app.route("/signup")
def get_signup():
    if is_logged_in():
        return redirect("/")
    return send_from_directory("static", "signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    global redis_client
    # check if user is already signed in
    if "username" in session:
        return jsonify({"error": "User is already signed in"}), 400
    # filter user input
    if (
        len(request.json["username"]) < 6
        or len(request.json["username"]) > 15
        or len(request.json["password"]) < 8
        or len(request.json["password"]) > 20
    ):
        return jsonify({"error": "Bad username or password"}), 400

    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (request.json["username"],)
    )
    user = cursor.fetchone()
    if user is not None:
        connection.close()
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.hashpw(
        request.json["password"].encode("utf-8"), bcrypt.gensalt()
    )
    cursor.execute(
        "INSERT INTO users (username, passhash) VALUES (?, ?)",
        (request.json["username"], hashed_password),
    )
    connection.commit()
    # get user id
    cursor.execute(
        "SELECT id FROM users WHERE username = ?", (request.json["username"],)
    )
    user = cursor.fetchone()[0]

    connection.close()
    session_token = os.urandom(24).hex()
    redis_client.set(session_token, user)
    session["token"] = session_token
    # user successfully created account, display home page
    return jsonify({"success": "User created successfully"}), 200


@app.route("/signin", methods=["POST"])
def login():
    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (request.json["username"],)
    )
    # check if user exists
    user = cursor.fetchone()
    if user is None:
        # dummy check to equalize response time (prevent timing attack)
        bcrypt.checkpw(
            request.json["password"].encode("utf-8"),
            b"$2b$12$eUhSqBS3J/ZqoZFZW/iOWe/P7JlBybwNDIZTbflwUajSqr0d6vlce",
        )
        connection.close()
        return jsonify({"error": "Incorrect username or password"}), 401

    if bcrypt.checkpw(
        request.json["password"].encode("utf-8"), user[2].encode("utf-8")
    ):
        session_token = os.urandom(24).hex()
        redis_client.set(session_token, user[0])
        session["token"] = session_token
        connection.close()
        return jsonify({"success": "Login successful"}), 200
    connection.close()
    return jsonify({"error": "Incorrect username or password"}), 401


@app.route("/signout", methods=["GET"])
def signout():
    global redis_client
    session_token = session.get("token")
    if session_token is None:
        return jsonify({"error": "User is not signed in"}), 400
    redis_client.delete(session_token)
    session.pop("token", None)
    return redirect("/")


@app.route("/file_request/<path:filename>", methods=["GET"])
def file_request(filename):
    uploads = os.path.join(current_app.root_path, "gym_resources")
    file_path = os.path.join(uploads, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
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


@app.route("/gym")
def get_gym():
    completed_ex = []
    if is_logged_in():
        connection = sqlite3.connect("users.sqlite")
        cur = connection.cursor()
        cur.execute(
            "SELECT completedproblems FROM users WHERE id = ?",
            (redis_client.get(session.get("token"))),
        )
        try:
            completed_ex = [
                int(prob) for prob in cur.fetchone()[0].strip("[]").split(",")
            ]
        except:
            completed_ex = []
        connection.close()
    # get gym data
    all_ex = []
    for i, filename in enumerate(
        sorted(os.listdir("gym_resources"), key=lambda x: int(x[0]))
    ):
        with open(f"gym_resources/{filename}/exercise.json", "r") as ex_file:
            ex_dict = json.load(ex_file)
            if i in completed_ex:
                ex_dict["completed"] = True
            else:
                ex_dict["completed"] = False
            all_ex.append(ex_dict)

    # get username
    user_id = redis_client.get(session.get("token"))
    connection = sqlite3.connect("users.sqlite")
    cur = connection.cursor()
    cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    uname = cur.fetchone()[0]
    connection.close()
    uname = "Welcome, " + uname
    if is_logged_in():
        return render_template("gym.html", uname=uname, exercises=all_ex)
    else:
        return render_template("gym.html", exercises=all_ex)


@app.route("/exercise/<path:ex_id>")
def get_exercise(ex_id):
    # filter user input
    try:
        ex_id = int(ex_id)
    except:
        return jsonify({"error": "Invalid exercise id"}), 400

    # get gym data
    if ex_id > len(os.listdir("gym_resources")):
        return jsonify({"error": "Invalid exercise id"}), 400

    with open(
        f"gym_resources/{sorted(os.listdir('gym_resources'), key=lambda x: int(x[0]))[ex_id - 1]}/exercise.json",
        "r",
    ) as ex_file:
        ex_dict = json.load(ex_file)
    return render_template("exercise.html", exercise=ex_dict)


@app.route("/probdone", methods=["POST"])
# TODO: change to function, not route- only call when answer submitted
def probdone():
    prob_id = request.form["prob_id"]
    if not is_logged_in():
        return jsonify({"error": "Not logged in"}), 401

    # filter user input
    try:
        prob_id = int(prob_id)
    except:
        return jsonify({"error": "Invalid problem id"}), 400

    if prob_id > len(os.listdir("gym_resources")):
        return jsonify({"error": "Invalid problem id"}), 400

    # connect to db
    connection = sqlite3.connect("users.sqlite")
    cur = connection.cursor()
    # get user info
    cur.execute(
        "SELECT completedproblems, gympoints FROM users WHERE id = ?",
        (redis_client.get(session.get("token"))),
    )
    db_res = cur.fetchone()
    probs = db_res[0].strip("[]").split(", ")
    # parse: len 0 will return []
    try:
        probs = [int(prob) for prob in probs]
    except:
        probs = []
    if prob_id in probs:
        return jsonify({"error": "Problem already completed"}), 400
    # add problem to problems
    probs.append(int(prob_id))
    # get curr amount of points
    curr_pts = int(db_res[1])
    resource_folder_path = sorted(os.listdir("gym_resources"), key=lambda x: int(x[0]))[
        prob_id - 1
    ]
    with open(
        f"gym_resources/{resource_folder_path}/exercise.json", "r"
    ) as points_file:
        points = json.load(points_file)["points"]
    # update db: add points, mark completed problem
    connection.executescript(
        f"UPDATE users SET completedproblems = '{probs}', gympoints = {curr_pts + points} WHERE id={redis_client.get(session.get('token'))}"
    )
    connection.commit()
    connection.close()
    return jsonify({"success": "Problem added"}), 200


if __name__ == "__main__":
    app.run(port=8080, debug=True)
