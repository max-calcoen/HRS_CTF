from flask import Flask, request
import sqlite3
from os import getenv

PORT = 2800

app = Flask(__name__)


@app.route("/")
def index():
    return "is this the right route?"


@app.route("/SQLAdmin", methods=["POST"])
def SQLAdmin():
    try:
        if not request.form["query"].startswith("SELECT"):
            return "ERROR: not an SQL SELECT query"
    except:
        return "ERROR: no query supplied"
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    try:
        cursor.execute(request.form["query"])
    except:
        return "ERROR: query failed"
    return cursor.fetchall()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(getenv("PORT", PORT)), debug=True)
