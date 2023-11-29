from fileinput import filename
import os
from flask import Flask, current_app, send_from_directory, session, request  # type: ignore
import secrets
import sqlite3

app = Flask(__name__, static_url_path="")
app.secret_key = secrets.token_hex()


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/login", methods=["POST"])
def login():
    # check if user exists
    connection = sqlite3.connect("users.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username = ?", (request.json["username"],)
    )
    user = cursor.fetchone()
    if user is None:
        return "User not found"

    # check if password is correct
    if user[2] != request.json["password"]:
        return "Incorrect password"

    return "Logged in"


@app.route("/file_request/<path:filename>", methods=["POST"])
def file_request(filename):
    uploads = os.path.join(current_app.root_path, "server_resources")
    file_path = os.path.join(uploads, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(uploads, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(port=8080, debug=True)
