from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    pass


@app.route("/leaderboard")
def leaderboard():
    pass


@app.route("/profile")
def profile():
    pass


if __name__ == "__main__":
    app.run(port=5000, debug=True)
