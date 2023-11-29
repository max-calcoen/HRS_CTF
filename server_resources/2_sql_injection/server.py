from flask import Flask, request
import sqlite3

PORT = 2800

app = Flask(__name__)


@app.route("/SQLAdmin", methods=["POST"])
def SQLAdmin():
    if not request.form["query"] or not request.form["query"].startswith("SELECT"):
        return "ERROR: not an SQL SELECT query"
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    try:
        cursor.execute(request.form["query"])
    except:
        return "ERROR: query failed"
    return [i[1] for i in cursor.fetchall()]


if __name__ == "__main__":
    app.run(port=PORT)
