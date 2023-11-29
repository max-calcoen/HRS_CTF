from fileinput import filename
import os
from flask import Flask, current_app, send_from_directory  # type: ignore

app = Flask(__name__, static_url_path="")


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/login", methods=["POST"])
def login():
    pass


@app.route("/file_request/<path:filename>", methods=["POST"])
def file_request(filename):
    uploads = os.path.join(current_app.root_path, "server_resources")
    file_path = os.path.join(uploads, filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(uploads, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(port=8080, debug=True)
