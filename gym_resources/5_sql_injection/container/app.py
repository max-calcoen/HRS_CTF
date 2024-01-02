from flask import Flask, request
import sqlite3
from os import getenv

PORT = 2800

app = Flask(__name__)


@app.route("/")
def home():
    return "hello"


@app.route("/SQLAdmin", methods=["POST"])
def SQLAdmin():
    print("recieved")
    try:
        print(request.form)
        print(request.json)
    except:
        print("error")
    try:
        if not request.form["query"].startswith("SELECT"):
            print("not sql query")
            return "ERROR: not an SQL SELECT query"
    except:
        return "ERROR: no query supplied"
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    try:
        cursor.execute(request.form["query"])
    except:
        return "ERROR: query failed"
    return [i[1] for i in cursor.fetchall()]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(getenv("PORT", 2800)), debug=True)
