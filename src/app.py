from datetime import datetime
import os
import glob
import subprocess
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_from_directory
)

from config import Config
from immich_api import Immich
from scanner import AlbumScanner
from album_sync import AlbumSync
from asset_cache import AssetCache
from album_rules import AlbumRules
from sync_report import SyncReport
from import_report import ImportReport


app = Flask(__name__)


APP_VERSION = "1.2.0"


# ============================================================
# VERSION
# ============================================================

@app.context_processor
def inject_version():

    return {
        "app_version": APP_VERSION
    }


# ============================================================
# SYNCHRONISATIONSBERICHTE
# ============================================================

def get_report_files(limit=3):

    report_dir = "/config/reports"

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

    for file in reports[:limit]:

        name = os.path.basename(file)

        stamp = name[:19]

        try:

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

    return files


# ============================================================
# IMPORT-REPORTS
# ============================================================

def get_import_report_files(limit=3):

    report_dir = "/config/reports"

    pattern = os.path.join(
        report_dir,
        "????-??-??_??-??-??_import_report.json"
    )

    reports = sorted(
        glob.glob(pattern),
        key=os.path.getmtime,
        reverse=True
    )

    files = []

    for file in reports[:limit]:

        name = os.path.basename(file)

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

    return files


# ============================================================
# IMPORT-LOGS
# ============================================================

def get_import_log_files(limit=3):

    log_dir = "/logs/family-photo-importer"

    pattern = os.path.join(
        log_dir,
        "import-????-??-??.log"
    )

    logs = sorted(
        glob.glob(pattern),
        key=os.path.getmtime,
        reverse=True
    )

    files = []

    for file in logs[:limit]:

        name = os.path.basename(file)

        try:

            date_part = name[
                len("import-"):
                len("import-") + 10
            ]

            dt = datetime.strptime(
                date_part,
                "%Y-%m-%d"
            )

            display = dt.strftime(
                "%d.%m.%Y"
            )

        except ValueError:

            display = name

        files.append({

            "file": name,

            "display": display

        })

    return files


# ============================================================
# STARTSEITE
# ============================================================

@app.route("/")
def index():

    cfg = Config.load()

    report_dir = "/config/reports"

    #
    # Synchronisationsberichte
    #

    reports = get_report_files(3)

    #
    # Letzter Synchronisationsbericht
    #

    last_report = os.path.join(
        report_dir,
        "last_sync_report.html"
    )

    last_report_exists = os.path.exists(
        last_report
    )

    #
    # Importberichte
    #

    import_reports = get_import_report_files(3)

    #
    # Letzter Importbericht
    #

    last_import_report = os.path.join(
        report_dir,
        "last_import_report.json"
    )

    last_import_report_exists = os.path.exists(
        last_import_report
    )

    #
    # Import-Logs
    #

    import_logs = get_import_log_files(3)

    #
    # Letzter Import-Log
    #

    last_import_log = None

    if import_logs:

        last_import_log = import_logs[0]["file"]

    return render_template(

        "index.html",

        config=cfg,

        reports=reports,

        last_report_exists=last_report_exists,

        import_reports=import_reports,

        last_import_report_exists=last_import_report_exists,

        import_logs=import_logs,

        last_import_log=last_import_log

    )


# ============================================================
# KONFIGURATION SPEICHERN
# ============================================================

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

        enabled = (
            request.form.get(
                f"enabled{i}"
            ) == "on"
        )

        if path:

            roots.append({

                "path": path,
                "mode": mode,
                "enabled": enabled

            })

        i += 1

    cfg["album_roots"] = roots

    Config.save(cfg)

    return redirect(
        url_for("index")
    )


# ============================================================
# FOTOIMPORT
# ============================================================

@app.route("/run_import", methods=["POST"])
def run_import():

    script = "/family-photo-importer/run-import.sh"

    # ========================================================
    # SCRIPT PRÜFEN
    # ========================================================

    if not os.path.isfile(script):

        return jsonify({
            "success": False,
            "error": f"Import-Script nicht gefunden: {script}"
        }), 500

    if not os.access(script, os.X_OK):

        return jsonify({
            "success": False,
            "error": f"Import-Script ist nicht ausführbar: {script}"
        }), 500

    # ========================================================
    # IMPORT STARTEN
    # ========================================================

    try:

        env = os.environ.copy()

        # Kennzeichnung für run-import.sh
        env["IMPORT_SOURCE"] = "WEB"

        result = subprocess.run(

            ["/bin/sh", script],

            cwd="/family-photo-importer",

            capture_output=True,

            text=True,

            timeout=1800,

            env=env
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # ====================================================
        # IMPORT_RESULT_JSON AUS stdout EXTRAHIEREN
        # ====================================================

        import_result = None

        for line in stdout.splitlines():

            if line.startswith("IMPORT_RESULT_JSON="):

                json_text = line[
                    len("IMPORT_RESULT_JSON="):
                ].strip()

                try:

                    import_result = json.loads(
                        json_text
                    )

                except json.JSONDecodeError:

                    import_result = None

        # ====================================================
        # REPORT-VERZEICHNIS
        # ====================================================

        report_dir = "/config/reports"

        os.makedirs(
            report_dir,
            exist_ok=True
        )

        # ====================================================
        # IMPORT-REPORT ERZEUGEN
        # ====================================================

        if import_result is not None:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            report_data = {

                "timestamp": timestamp,

                "source": "WEB",

                "result": import_result

            }

            # ------------------------------------------------
            # Letzter Importbericht
            # ------------------------------------------------

            last_report = os.path.join(
                report_dir,
                "last_import_report.json"
            )

            with open(
                last_report,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    report_data,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            # ------------------------------------------------
            # Historischer Importbericht
            # ------------------------------------------------

            historical_report = os.path.join(
                report_dir,
                f"{timestamp}_import_report.json"
            )

            with open(
                historical_report,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    report_data,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        # ====================================================
        # AKTUELLSTEN LOG ERMITTELN
        # ====================================================

        log_dir = "/logs/family-photo-importer"

        log_file = None

        if os.path.isdir(log_dir):

            log_files = [

                os.path.join(
                    log_dir,
                    filename
                )

                for filename in os.listdir(log_dir)

                if filename.startswith("import-")
                and filename.endswith(".log")

            ]

            if log_files:

                log_file = max(
                    log_files,
                    key=os.path.getmtime
                )

        # ====================================================
        # IMPORT ERFOLGREICH
        # ====================================================

        if result.returncode == 0:

            return jsonify({

                "success": True,

                "message":
                    "Foto-Import erfolgreich abgeschlossen.",

                "returncode":
                    result.returncode,

                "import_result":
                    import_result,

                "log_file":
                    log_file,

                "output":
                    stdout[-4000:]

            })

        # ====================================================
        # IMPORT FEHLGESCHLAGEN
        # ====================================================

        return jsonify({

            "success": False,

            "error":
                "Importer beendet mit "
                f"Exit-Code {result.returncode}",

            "returncode":
                result.returncode,

            "import_result":
                import_result,

            "log_file":
                log_file,

            "output":
                stdout[-2000:]
                + "\n"
                + stderr[-2000:]

        }), 500

    # ========================================================
    # TIMEOUT
    # ========================================================

    except subprocess.TimeoutExpired:

        return jsonify({

            "success": False,

            "error":
                "Der Foto-Import läuft länger "
                "als 30 Minuten."

        }), 500

    # ========================================================
    # SONSTIGER FEHLER
    # ========================================================

    except Exception as ex:

        return jsonify({

            "success": False,

            "error": str(ex)

        }), 500


# ============================================================
# SCAN
# ============================================================

@app.route("/scan")
def scan():

    cfg = Config.load()

    scanner = AlbumScanner()

    if AssetCache.exists():

        scanner.set_asset_index(
            AssetCache.get_index()
        )

    albums = scanner.scan(
        cfg["album_roots"]
    )

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


    albums = sorted(

        albums,

        key=lambda a: (

            a["album"].lower(),

            a["year"] or ""

        )

    )


    cache_info = AssetCache.info()

    cache_exists = cache_info["exists"]


    return render_template(

        "scan.html",

        albums=albums,

        immich_ok=immich_ok,

        cache_exists=cache_exists,

        cache_info=cache_info

    )


# ============================================================
# SYNCHRONISATION
# ============================================================

@app.route("/sync")
def sync():

    cfg = Config.load()

    api = Immich(

        cfg["immich"]["url"],

        cfg["immich"]["api_key"]

    )

    asset_index = api.get_asset_index()

    AssetCache.save(asset_index)

    report = SyncReport()

    scanner = AlbumScanner()

    scanner.set_asset_index(asset_index)

    albums = scanner.scan(
        cfg["album_roots"]
    )

    sync = AlbumSync(

        api,

        report

    )

    albums = sync.compare(albums)

    albums = sync.prepare_assets(albums)

    created = sync.create_missing_albums(
        albums
    )

    updated = sync.update_existing_albums(
        albums
    )

    report_dir = "/config/reports"

    os.makedirs(
        report_dir,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    html = render_template(

        "sync_report.html",

        report=report.to_dict()

    )

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


    return render_template(

        "sync_report.html",

        report=report.to_dict()

    )


# ============================================================
# ALBUM-REGEL
# ============================================================

@app.route("/set_rule", methods=["POST"])
def set_rule_route():

    data = request.get_json()

    album = data.get("album")

    auto_add = data.get(
        "auto_add",
        False
    )

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


# ============================================================
# IMMICH TEST
# ============================================================

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


# ============================================================
# ASSET CACHE
# ============================================================

@app.route("/build_cache")
def build_cache():

    cfg = Config.load()

    api = Immich(

        cfg["immich"]["url"],

        cfg["immich"]["api_key"]

    )

    cache = api.get_asset_index(force=True)

    AssetCache.save(cache)

    return {

        "success": True,

        "assets": len(cache)

    }


# ============================================================
# API PROBE
# ============================================================

@app.route("/probe")
def probe():

    cfg = Config.load()

    api = Immich(

        cfg["immich"]["url"],

        cfg["immich"]["api_key"]

    )

    return api.api_probe()


# ============================================================
# SYNCHRONISATIONSBERICHTE
# ============================================================

@app.route("/reports")
def reports():

    files = get_report_files(
        limit=1000
    )

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


# ============================================================
# IMPORT-REPORT
# ============================================================

@app.route("/import_report/<filename>")
def import_report(filename):

    report_dir = "/config/reports"

    filepath = os.path.join(
        report_dir,
        filename
    )

    if not os.path.isfile(filepath):

        return (
            "Importbericht nicht gefunden.",
            404
        )

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            report = json.load(f)

    except Exception as ex:

        return (
            f"Importbericht konnte nicht gelesen werden: {ex}",
            500
        )

    return render_template(
        "import_report.html",
        report=report,
        filename=filename
    )


@app.route("/import_reports")
def import_reports():

    reports = get_import_report_files(
        limit=1000
    )

    return render_template(

        "import_reports.html",

        reports=reports

    )


# ============================================================
# IMPORT-LOG
#
# Nicht als Datei ausliefern!
#
# Stattdessen wird eine HTML-Seite erzeugt.
# ============================================================

@app.route("/import_log/<filename>")
def import_log(filename):

    log_dir = "/logs/family-photo-importer"

    filepath = os.path.join(
        log_dir,
        filename
    )

    if not os.path.isfile(filepath):

        return (
            "Import-Log nicht gefunden.",
            404
        )

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as f:

            log_content = f.read()

    except Exception as ex:

        return (
            f"Import-Log konnte nicht gelesen werden: {ex}",
            500
        )

    return render_template(
        "import_log.html",
        filename=filename,
        log_content=log_content
    )


# ============================================================
# IMPORT-LOGS
# ============================================================

@app.route("/import_logs")
def import_logs():

    logs = get_import_log_files(
        limit=1000
    )

    return render_template(

        "import_logs.html",

        logs=logs

    )


# ============================================================
# BERICHT-BEREINIGUNG
# ============================================================

def cleanup_files(pattern, keep=3):
    files = sorted(
        glob.glob(pattern),
        key=os.path.getmtime,
        reverse=True
    )

    deleted = 0

    for file in files[keep:]:
        try:
            os.remove(file)
            deleted += 1
        except OSError as ex:
            print(
                f"Fehler beim Löschen von {file}: {ex}"
            )

    return deleted


@app.route("/cleanup_reports")
def cleanup_reports():
    report_dir = "/config/reports"

    deleted_html = cleanup_files(
        os.path.join(
            report_dir,
            "????-??-??_??-??-??_sync_report.html"
        ),
        keep=3
    )

    deleted_txt = cleanup_files(
        os.path.join(
            report_dir,
            "????-??-??_??-??-??_sync_report.txt"
        ),
        keep=3
    )

    return redirect("/")


@app.route("/cleanup_import_reports")
def cleanup_import_reports():
    report_dir = "/config/reports"

    deleted = cleanup_files(
        os.path.join(
            report_dir,
            "????-??-??_??-??-??_import_report.json"
        ),
        keep=3
    )

    return redirect("/")


@app.route("/cleanup_import_logs")
def cleanup_import_logs():
    log_dir = "/logs/family-photo-importer"

    deleted = cleanup_files(
        os.path.join(
            log_dir,
            "import-????-??-??.log"
        ),
        keep=3
    )

    return redirect("/")


# ============================================================
# INFO
# ============================================================

@app.route("/info")
def info():

    return render_template(
        "info.html"
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5050

    )