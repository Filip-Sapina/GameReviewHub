from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World! This is the Game Reviews Hub, Find Out what other people say about games!</p>"
