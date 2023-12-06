from flask import Flask, redirect, send_file, request, render_template, jsonify  # type: ignore
from urllib.parse import unquote

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("login.htm")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.htm")


ex = [
    {"title": "Exercise 1", "description": "Description of Exercise 1"},
    {"title": "Exercise 2", "description": "Description of Exercise 2"},
]

# example prob: shift is five btw
caesar_cipher = {
    "title": "Caesar Cipher",
    "points": "5",
    "description": "Decode the following message",
    "hint": "Try shifting each letter by a certain number, and if the resulting characters form a coherent phrase",
    "files": ["static/Exercises/caesar_cipher_1/ciphertext.txt"],
}


@app.route("/gym")
def gym():
    return render_template("gym.htm", exercises=ex)


@app.route("/ex")
def exercise():
    return render_template("exercise.htm", exercise=caesar_cipher)


@app.route("/submit_flag", methods=["POST"])
def submit():
    if "mjqqt" == request.form["flag_input"]:
        return "SUCCESSFUL"
    else:
        return "WRONG"


if __name__ == "__main__":
    app.run(port=4242)
