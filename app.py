from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Maintenance Ticketing System"


@app.route("/health")
def health():
    return {"status": "ok"}
