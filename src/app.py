from flask import Flask, render_template, request, redirect, url_for
from immich_api import Immich
from scanner import Scanner
from config import Config

app = Flask(__name__)


@app.route("/")
def index():
    cfg = Config.load()
    return render_template("index.html", config=cfg)


@app.route("/save", methods=["POST"])
def save():

    cfg = Config.load()

    cfg["immich_url"] = request.form.get("immich_url", "").strip()
    cfg["api_key"] = request.form.get("api_key", "").strip()

    roots = []

    i = 0
    while True:
        key = f"root{i}"
        if key not in request.form:
            break

        path = request.form[key].strip()

        if path:
            roots.append({
                "path": path,
                "recursive": True
            })

        i += 1

    cfg["album_roots"] = roots

    Config.save(cfg)

    return redirect(url_for("index"))


@app.route("/scan")
def scan():

    cfg = Config.load()

    scanner = Scanner()

    folders = scanner.scan(
        cfg["album_roots"]
    )

    return render_template(
        "scan.html",
        folders=folders
    )

@app.route("/test")
def test():

    cfg = Config.load()

    api = Immich(
        cfg["immich_url"],
        cfg["api_key"]
    )

    ok = api.test_connection()

    return {
        "connected": ok
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)