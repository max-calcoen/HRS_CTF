import json
import atexit
import os
import secrets
import socket
import sqlite3
import threading
from subprocess import Popen

import bcrypt
import docker
import redis
from flask import (
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from DatabaseManager import DatabaseManager
from User import User

# Initialize the Flask application
app = Flask(__name__, static_url_path="")
app.secret_key = secrets.token_hex()

# Connect to Redis database for session management
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Create a Docker client connected to the local Docker daemon
docker_client = docker.from_env()

# Global dictionary to keep track of active Docker containers
containers = {}

# Initialize the DatabaseManager for handling users' data
users_dbm = DatabaseManager("users.sqlite")


def is_logged_in():
    """
    Check if the current user is logged in by verifying the session token in Redis.

    Returns:
        The user ID if logged in, False otherwise.
    """
    global redis_client
    session_token = session.get("token")
    # Check if token exists and matches session cache
    return (
        redis_client.get(session_token)
        if session_token is not None and redis_client.get(session_token) is not None
        else False
    )


@app.route("/")
def home():
    """
    Home route that renders the main page. If the user is logged in, it fetches the user's
    information such as username and points from the database and passes it to the template.

    Returns:
        Rendered template of the main page.
    """
    global users_dbm
    if not is_logged_in():
        return render_template("index.html")
    user_id = redis_client.get(session.get("token"))
    user = users_dbm.get_user(user_id)
    username = user.username
    points = user.points
    return render_template("index.html", username=username, points=points)


@app.route("/signin")
def signin():
    """
    Sign-in route that renders the sign-in page if the user is not already logged in.

    Returns:
        Rendered template of the sign-in page or redirect to home if already logged in.
    """
    if is_logged_in():
        return redirect("/")
    return send_from_directory("static", "signin.html")


@app.route("/signup")
def get_signup():
    """
    Sign-up route that renders the sign-up page if the user is not already logged in.

    Returns:
        Rendered template of the sign-up page or redirect to home if already logged in.
    """
    if is_logged_in():
        return redirect("/")
    return send_from_directory("static", "signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    """
    POST route for signing up a new user. It validates the input data, checks if the username
    is taken, hashes the password, and creates a new user in the database.

    Returns:
        JSON response indicating success or failure.
    """
    global redis_client
    # Check if user is already signed in
    if "username" in session:
        return jsonify({"error": "User is already signed in"}), 400
    # Validate user input
    if (
        len(request.json["username"]) < 6
        or len(request.json["username"]) > 15
        or len(request.json["password"]) < 8
        or len(request.json["password"]) > 20
    ):
        return jsonify({"error": "Bad username or password"}), 400

    # Check if user already exists
    user = users_dbm.get_user(users_dbm.get_user_id(request.json["username"]))
    if user is not None:
        return jsonify({"error": "User already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(
        request.json["password"].encode("utf-8"), bcrypt.gensalt()
    )
    # Create a new user instance
    user = User((0, request.json["username"], hashed_password, 0, "[]"))
    u_id = users_dbm.add_user(user)

    # Create a session token and store it in Redis
    session_token = os.urandom(24).hex()
    redis_client.set(session_token, u_id)
    session["token"] = session_token

    return jsonify({"success": "User created successfully"}), 200


@app.route("/signin", methods=["POST"])
def login():
    """
    POST route for signing in a user. It checks the username and password against the database,
    and if they match, it creates a session token and logs the user in.

    Returns:
        JSON response indicating success or failure.
    """
    user = users_dbm.get_user(users_dbm.get_user_id(request.json["username"]))

    if user is None:
        # Dummy check to equalize response time (prevent timing attack)
        bcrypt.checkpw(
            request.json["password"].encode("utf-8"),
            b"$2b$12$eUhSqBS3J/ZqoZFZW/iOWe/P7JlBybwNDIZTbflwUajSqr0d6vlce",
        )
        return jsonify({"error": "Incorrect username or password"}), 401

    if bcrypt.checkpw(request.json["password"].encode("utf-8"), user.password):
        session_token = os.urandom(24).hex()
        redis_client.set(session_token, user.id)
        session["token"] = session_token
        return jsonify({"success": "Login successful"}), 200
    return jsonify({"error": "Incorrect username or password"}), 401


@app.route("/signout", methods=["GET"])
def signout():
    """
    GET route for signing out a user. It removes the session token from Redis and the session.

    Returns:
        Redirects to the home page.
    """
    global redis_client
    session_token = session.get("token")
    if session_token is None:
        return jsonify({"error": "User is not signed in"}), 400
    redis_client.delete(session_token)
    session.pop("token", None)
    return redirect("/")


@app.route("/file_request/<path:ex_id>/<path:filename>", methods=["GET"])
def file_request(filename, ex_id):
    """
    Route to handle file requests for a given exercise. It serves files located in
    the gym_resources directory corresponding to a specific exercise.

    Args:
        filename: The name of the file being requested.
        ex_id: The ID of the exercise.

    Returns:
        The requested file or a JSON error message.
    """
    gym_path = os.path.join(current_app.root_path, "gym_resources")
    file_path = None
    # Iterate through gym_resources to find the requested file
    for path in os.listdir(gym_path):
        try:
            if int(path[0:2]) == int(ex_id):
                file_path = os.path.join(path, "public", filename)
                break
        except:
            return jsonify({"error": "Wrong exercise ID"}), 400

    if file_path is None:
        return jsonify({"error": "Wrong exercise ID"}), 400
    if not os.path.exists(os.path.join(gym_path, file_path)):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(gym_path, file_path, as_attachment=True)


@app.route("/request_container", methods=["POST"])
def request_container():
    """
    POST route to handle requests for starting a Docker container for an exercise. It
    checks if the user is logged in, verifies the exercise ID, and then starts the
    container using the specified image.

    Returns:
        JSON response indicating success or failure.
    """
    if not is_logged_in():
        return jsonify({"error": "User is not signed in"}), 400
    ex_id = request.json["ex_id"]
    # Find the specified exercise container
    abs_gym_path = os.path.join(current_app.root_path, "gym_resources")
    ex_path = None
    for path in os.listdir(abs_gym_path):
        try:
            if int(path[0:2]) == int(ex_id):
                ex_path = path
                break
        except:
            return jsonify({"error": "Wrong exercise ID"}), 400

    if os.path.join(ex_path, "container") is None:
        return jsonify({"error": "Wrong exercise ID"}), 400

    if not os.path.exists(
        os.path.join(abs_gym_path, os.path.join(ex_path, "container"))
    ):
        return jsonify({"error": "Container not found"}), 404

    user_id = redis_client.get(session.get("token"))
    # Check if user already has an active container
    if containers.keys().__contains__(user_id):
        return redirect("/stop_container", code=307)

    # Extract image details and start the container
    with open(os.path.join(abs_gym_path, ex_path, "exercise.json"), "r") as ex_file:
        ex_dict = json.load(ex_file)
        image_name = ex_dict["imageName"]
        image_tag = ex_dict["imageTag"]
        image_port = ex_dict["imagePort"]

    # Start the container using the Docker client
    container = docker_client.containers.run(
        f"{image_name}:{image_tag}",
        name=f"user{user_id}-ex{ex_id}",
        ports={image_port: None},
        detach=True,
    )
    containers[user_id] = container
    return jsonify({"success": f"Container started successfully"}), 200


@app.route("/stop_container", methods=["POST"])
def stop_container():
    """
    POST route to stop the active Docker container for the user. It checks if the user
    is logged in and if there is an active container, then stops and removes it.

    Returns:
        JSON response indicating success or failure.
    """
    if not is_logged_in():
        return jsonify({"error": "User is not signed in"}), 400
    user_id = redis_client.get(session.get("token"))
    if not containers.keys().__contains__(user_id):
        return jsonify({"error": "User does not have an active container"}), 400

    containers[user_id].stop()
    containers[user_id].remove()
    containers.pop(user_id)
    return jsonify({"success": "Container stopped"}), 200

@app.route("/gym")
def get_gym():
    """
    Route to display the gym page where users can see and select exercises. It retrieves
    the list of all exercises and marks those that have been completed by the user.
    
    Returns:
        Rendered gym template with exercises information or redirects to the sign-in page.
    """
    completed_ex = []
    session_token = session.get("token")

    if session_token is None:
        return redirect("/signin")

    user_id = redis_client.get(session_token)
    if user_id is None:
        return redirect("/signin")

    user = users_dbm.get_user(user_id)
    if is_logged_in():
        completed_ex = user.completed_ex
    # Retrieve all exercises and their completion status
    all_ex = []
    for i, filename in enumerate(
        sorted(os.listdir("gym_resources"), key=lambda x: int(x[0:2]))
    ):
        with open(f"gym_resources/{filename}/exercise.json", "r") as ex_file:
            ex_dict = json.load(ex_file)
            if i + 1 in completed_ex:
                ex_dict["completed"] = True
            else:
                ex_dict["completed"] = False
            all_ex.append(ex_dict)

    if is_logged_in():
        return render_template(
            "gym.html", uname=user.username, exercises=all_ex, points=user.points
        )
    else:
        return render_template("gym.html", exercises=all_ex)


@app.route("/exercise/<path:ex_id>")
def get_exercise(ex_id):
    """
    Route to display a specific exercise's page. It retrieves the exercise details
    from the gym_resources directory based on the provided exercise ID.

    Args:
        ex_id: The ID of the exercise.

    Returns:
        Rendered exercise template with the exercise details or an error message.
    """
    try:
        ex_id = int(ex_id)  # Ensure the exercise ID is an integer
    except ValueError:
        return jsonify({"error": "Invalid exercise id"}), 400

    if ex_id > len(os.listdir("gym_resources")) or ex_id < 1:
        return jsonify({"error": "Invalid exercise id"}), 400
    with open(
        f"gym_resources/{sorted(os.listdir('gym_resources'), key=lambda x: int(x[0:2]))[ex_id - 1]}/exercise.json",
        "r",
    ) as ex_file:
        ex_dict = json.load(ex_file)
        ex_dict["ex_id"] = ex_id
    return render_template("exercise.html", exercise=ex_dict)


@app.route("/flag", methods=["POST"])
def submit_flag():
    """
    POST route to handle the submission of a flag by the user for a specific exercise.
    It validates the user's session, checks the provided flag against the correct one,
    and updates the user's completion status and points if correct.

    Returns:
        JSON response indicating success or failure of the flag submission.
    """
    try:
        ex_id = int(request.json["ex_id"])
        if ex_id > len(os.listdir("gym_resources")) or ex_id < 1:
            raise ValueError("Invalid exercise id")
    except ValueError:
        return jsonify({"error": "Invalid exercise id"}), 400

    session_token = session.get("token")
    if session_token is None:
        return jsonify({"error": "Sign in to complete this exercise!"}), 400

    user_id = redis_client.get(session_token)
    if user_id is None:
        return jsonify({"error": "Invalid session token"}), 400

    # Validate the submitted flag
    resource_folder_path = sorted(
        os.listdir("gym_resources"), key=lambda x: int(x[0:2])
    )[ex_id - 1]
    with open(f"gym_resources/{resource_folder_path}/exercise.json", "r") as ex_file:
        ex_dict = json.load(ex_file)

    if ex_dict["flag"] == request.json["flag"]:
        if handle_completed_ex(ex_id, user_id):
            return jsonify({"success": "Flag correct!"}), 200
        else:
            return jsonify({"error": "Exercise already completed!"}), 400
    return jsonify({"error": "Flag incorrect!"}), 400


def handle_completed_ex(ex_id, user_id):
    """
    Helper function to handle the completion of an exercise by a user. It updates the
    user's completed exercises list and points in the database.

    Args:
        ex_id: The ID of the exercise.
        user_id: The ID of the user.

    Returns:
        True if the exercise was successfully marked as completed, False otherwise.
    """
    global users_dbm
    user = users_dbm.get_user(user_id)
    exs = user.completed_ex
    if ex_id in exs:
        return False  # Exercise already completed

    exs.append(int(ex_id))  # Mark the exercise as completed

    # Update user's points based on the exercise's point value
    resource_folder_path = sorted(
        os.listdir("gym_resources"), key=lambda x: int(x[0:2])
    )[ex_id - 1]
    with open(
        f"gym_resources/{resource_folder_path}/exercise.json", "r"
    ) as points_file:
        points = json.load(points_file)["points"]

    user.completed_ex.append(ex_id)
    user.points += points
    users_dbm.update_user(user)
    return True


@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    """
    Route to display the leaderboard, showing users sorted by their points.
    It requires the user to be logged in to view.

    Returns:
        Rendered leaderboard template or an error message.
    """
    session_token = session.get("token")
    if session_token is None:
        return jsonify({"error": "Sign in to view the leaderboard!"}), 400

    users = users_dbm.get_users()
    users = sorted(users, key=lambda user: user.points, reverse=True)

    users_list = [
        {"rank": i + 1, "username": user.username, "gympoints": user.points}
        for i, user in enumerate(users)
    ]
    return render_template("leaderboard.html", sorted_players=users_list)


@atexit.register
def goodbye():
    """
    This function is registered to execute when the application exits.
    It ensures that any active Docker containers are stopped and removed.
    """
    for container in containers.values():
        container.stop()
        container.remove()


if __name__ == "__main__":
    app.run(port=8080)
