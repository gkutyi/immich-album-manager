from datetime import datetime
import os
import glob

from flask import Flask, render_template, request, redirect, url_for, jsonify, render_template_string, send_from_directory

from config import Config
from immich_api import Immich
from scanner import AlbumScanner
from album_sync import AlbumSync
from asset_cache import AssetCache
from album_rules import AlbumRules
from sync_report import SyncReport

app = Flask(__name__)

APP_VERSION = "1.0.0"


@app.context_processor
def inject_version():

    return {
        "app_version": APP_VERSION
    }


def get_report_files(limit=3):

    report_dir = "/config/reports"

    reports = sorted(

        glob.glob(
            os.path.join(
                report_dir,
                "*_sync_report.html"
            )
        ),

        key=os.path.getmtime,

        reverse=True

    )

    files = []

    for file in reports:

        name = os.path.basename(file)

        #
        # Zeitstempel aus Dateinamen
        #

        try:

            stamp = name[:19]

            dt = datetime.strptime(
                stamp,
                "%Y-%m-%d_%H-%M-%S"
            )

            display = dt.strftime(
                "%d.%m.%Y %H:%M:%S"
            )

        except ValueError:

            display = name

        files.append({

            "file": name,

            "display": display

        })

    return files[:limit]

@app.route("/")
def index():

    cfg = Config.load()

    report_dir = "/config/reports"

    #
    # Historische Reports ermitteln
    #

    pattern = os.path.join(
        report_dir,
        "????-??-??_??-??-??_sync_report.html"
    )

    reports = sorted(

        glob.glob(pattern),

        key=os.path.getmtime,

        reverse=True

    )

    report_files = []

    for file in reports[:3]:

        name = os.path.basename(file)

        stamp = name[:19]

        try:

            dt = datetime.strptime(
                stamp,
                "%Y-%m-%d_%H-%M-%S"
            )

        except ValueError:

            continue

        report_files.append({

            "file": name,

            "display": dt.strftime(
                "%d.%m.%Y %H:%M:%S"
            )

        })

    #
    # Gibt es einen aktuellen Bericht?
    #

    last_report = os.path.join(
        report_dir,
        "last_sync_report.html"
    )

    last_report_exists = os.path.exists(
        last_report
    )

    return render_template(

        "index.html",

        config=cfg,

        reports=report_files,

        last_report_exists=last_report_exists

    )

@app.route("/save", methods=["POST"])
def save():

    cfg = Config.load()

    #
    # Immich
    #

    cfg["immich"]["url"] = request.form.get(
        "immich_url",
        ""
    ).strip()

    cfg["immich"]["api_key"] = request.form.get(
        "api_key",
        ""
    ).strip()

    #
    # Album-Regeln
    #

    roots = []

    i = 0

    while True:

        path_key = f"path{i}"

        if path_key not in request.form:
            break

        path = request.form[path_key].strip()

        mode = request.form.get(
            f"mode{i}",
            "children"
        )

        enabled = request.form.get(
            f"enabled{i}"
        ) == "on"

        if path:

            roots.append({
                "path": path,
                "mode": mode,
                "enabled": enabled
            })

        i += 1

    cfg["album_roots"] = roots

    Config.save(cfg)

    return redirect(url_for("index"))


@app.route("/scan")
def scan():

    cfg = Config.load()

    #
    # Scanner starten
    #

    scanner = AlbumScanner()
    
    #
    # Asset-Cache laden
    #

    if AssetCache.exists():

        scanner.set_asset_index(

            AssetCache.get_index()

        )

    albums = scanner.scan(

        cfg["album_roots"]

    )

    #
    # Mit Immich vergleichen
    #

    immich_ok = False

    try:

        api = Immich(
            cfg["immich"]["url"],
            cfg["immich"]["api_key"]
        )

        immich_ok = api.test_connection()

        if immich_ok:

            sync = AlbumSync(api)

            albums = sync.compare(albums)

    except Exception as ex:

        print(ex)
    

    #
    # Nach Albumname sortieren
    #

    albums = sorted(
        albums,
        key=lambda a: (
            a["album"].lower(),
            a["year"] or ""
        )
    )

    #
    # Cache-Informationen
    #

    cache_info = AssetCache.info()

    cache_exists = cache_info["exists"]

    return render_template(

        "scan.html",

        albums=albums,

        immich_ok=immich_ok,

        cache_exists=cache_exists,

        cache_info=cache_info

    )

@app.route("/sync")
def sync():

    cfg = Config.load()

    #
    # Immich
    #

    api = Immich(
        cfg["immich"]["url"],
        cfg["immich"]["api_key"]
    )

    #
    # Asset-Cache aktualisieren
    #

    asset_index = api.get_asset_index()
    
    AssetCache.save(asset_index)

    #
    # Report
    #

    report = SyncReport()
    
    #
    # Scanner
    #
    
    scanner = AlbumScanner()

    scanner.set_asset_index(asset_index)

    albums = scanner.scan(
        cfg["album_roots"]
    )

    sync = AlbumSync(

        api,

        report

    )

    #
    # Vergleich
    #
    
    albums = sync.compare(albums)
    
    albums = sync.prepare_assets(albums)

    #
    # Fehlende Alben erzeugen
    #

    created = sync.create_missing_albums(
        albums
    )

    #
    # Fehlende Assets ergänzen
    #

    updated = sync.update_existing_albums(
        albums
    )
    
    #
    # Berichtsordner anlegen
    #

    report_dir = "/config/reports"

    os.makedirs(
        report_dir,
        exist_ok=True
    )

    #
    # Zeitstempel erzeugen
    #

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    #
    # HTML erzeugen
    #

    html = render_template(

        "sync_report.html",

        report=report.to_dict()

    )

    #
    # HTML speichern
    #

    with open(

        os.path.join(
            report_dir,
            "last_sync_report.html"
        ),

        "w",

        encoding="utf-8"

    ) as f:

        f.write(html)


    with open(

        os.path.join(
            report_dir,
            f"{timestamp}_sync_report.html"
        ),

        "w",

        encoding="utf-8"

    ) as f:

        f.write(html)

    #
    # TXT speichern
    #

    report.save(

        os.path.join(
            report_dir,
            "last_sync_report.txt"
        )

    )

    report.save(

        os.path.join(
            report_dir,
            f"{timestamp}_sync_report.txt"
        )

    )
    
    #
    # Alte Reports löschen
    #

    html_reports = sorted(

        glob.glob(

            os.path.join(
                report_dir,
                "*_sync_report.html"
            )

        ),

        key=os.path.getmtime,

        reverse=True

    )

    txt_reports = sorted(

        glob.glob(

            os.path.join(
                report_dir,
                "*_sync_report.txt"
            )

        ),

        key=os.path.getmtime,

        reverse=True

    )

    return render_template(

        "sync_report.html",

        report=report.to_dict()

    )
    
@app.route("/set_rule", methods=["POST"])
def set_rule_route():

    data = request.get_json()

    album = data.get("album")
    auto_add = data.get("auto_add", True)

    if not album:
        return jsonify({
            "success": False,
            "error": "Album fehlt"
        }), 400

    AlbumRules.set(
        album,
        auto_add=auto_add
    )

    return jsonify({
        "success": True
    })

@app.route("/test")
def test():

    cfg = Config.load()

    api = Immich(
        cfg["immich"]["url"],
        cfg["immich"]["api_key"]
    )

    ok = api.test_connection()

    return {
        "connected": ok
    }
    
@app.route("/build_cache")
def build_cache():

    cfg = Config.load()

    api = Immich(

        cfg["immich"]["url"],
        cfg["immich"]["api_key"]

    )

    cache = api.get_asset_index()

    AssetCache.save(cache)

    return {

        "success": True,

        "assets": len(cache)

    }
    
@app.route("/probe")
def probe():

    cfg = Config.load()

    api = Immich(

        cfg["immich"]["url"],

        cfg["immich"]["api_key"]

    )

    return api.api_probe()


@app.route("/reports")
def reports():

    report_dir = "/config/reports"

    #
    # Nur echte zeitgestempelte Reports berücksichtigen.
    # last_sync_report.html wird bewusst ausgeschlossen.
    #

    pattern = os.path.join(
        report_dir,
        "????-??-??_??-??-??_sync_report.html"
    )

    reports = sorted(
        glob.glob(pattern),
        key=os.path.getmtime,
        reverse=True
    )

    files = []

    for file in reports[:3]:

        name = os.path.basename(file)

        stamp = name[:19]

        try:

            dt = datetime.strptime(
                stamp,
                "%Y-%m-%d_%H-%M-%S"
            )

        except ValueError:

            continue

        files.append({

            "file": name,

            "display": dt.strftime(
                "%d.%m.%Y %H:%M:%S"
            )

        })

    return render_template(

        "reports.html",

        reports=files

    )
    
@app.route("/report/<filename>")
def report(filename):

    return send_from_directory(

        "/config/reports",

        filename

    )
    
@app.route("/cleanup_reports")
def cleanup_reports():

    report_dir = "/config/reports"

    #
    # HTML
    #

    html_reports = sorted(

        glob.glob(

            os.path.join(
                report_dir,
                "*_sync_report.html"
            )

        ),

        key=os.path.getmtime,

        reverse=True

    )

    #
    # TXT
    #

    txt_reports = sorted(

        glob.glob(

            os.path.join(
                report_dir,
                "*_sync_report.txt"
            )

        ),

        key=os.path.getmtime,

        reverse=True

    )

    #
    # alles außer den letzten 3 löschen
    #

    for file in html_reports[3:]:

        if os.path.exists(file):

            os.remove(file)

    for file in txt_reports[3:]:

        if os.path.exists(file):

            os.remove(file)

    return redirect("/")

@app.route("/info")
def info():

    return render_template(
        "info.html"
    )
    

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5050
    )
