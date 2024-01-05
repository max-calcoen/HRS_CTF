import flask


app = flask.Flask(__name__)


@app.route("/", methods=["GET"])
def red():
    return flask.send_file("red.html")


@app.route("/", methods=["POST"])
def blue():
    return flask.send_file("blue.html")


@app.route("/", methods=["TRACE"])
def flag():
    return "hrsCTF{GET_outta_h3re}"


@app.route("/css")
def css():
    return flask.send_file("style.css")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2800)
