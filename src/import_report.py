import os
from datetime import datetime


class ImportReport:

    def __init__(self):

        self.total = 0
        self.dry_run = 0
        self.moved = 0
        self.no_date = 0
        self.exists = 0
        self.exists_deleted = 0
        self.exists_delete_error = 0
        self.ignored = 0

        self.status = "OK"
        self.immich_scan = "NICHT DURCHGEFÜHRT"

        self.timestamp = datetime.now()

    # ========================================================
    # AUS IMPORTER-ERGEBNIS ERZEUGEN
    # ========================================================

    @classmethod
    def from_dict(cls, data):

        report = cls()

        report.total = int(
            data.get("total", 0)
        )

        report.dry_run = int(
            data.get("dry_run", 0)
        )

        report.moved = int(
            data.get("moved", 0)
        )

        report.no_date = int(
            data.get("no_date", 0)
        )

        report.exists = int(
            data.get("exists", 0)
        )

        report.exists_deleted = int(
            data.get("exists_deleted", 0)
        )

        report.exists_delete_error = int(
            data.get("exists_delete_error", 0)
        )

        report.ignored = int(
            data.get("ignored", 0)
        )

        report.status = data.get(
            "status",
            "OK"
        )

        report.immich_scan = data.get(
            "immich_scan",
            "NICHT DURCHGEFÜHRT"
        )

        return report

    # ========================================================
    # DICT
    # ========================================================

    def to_dict(self):

        return {

            "timestamp":
                self.timestamp.strftime(
                    "%d.%m.%Y %H:%M:%S"
                ),

            "total":
                self.total,

            "dry_run":
                self.dry_run,

            "moved":
                self.moved,

            "no_date":
                self.no_date,

            "exists":
                self.exists,

            "exists_deleted":
                self.exists_deleted,

            "exists_delete_error":
                self.exists_delete_error,

            "ignored":
                self.ignored,

            "status":
                self.status,

            "immich_scan":
                self.immich_scan

        }

    # ========================================================
    # TXT
    # ========================================================

    def save_txt(self, filename):

        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        data = self.to_dict()

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "=" * 72 + "\n"
            )

            f.write(
                "Immich Album Manager - "
                "Fotoimportbericht\n"
            )

            f.write(
                "=" * 72 + "\n\n"
            )

            f.write(
                f"Datum             : "
                f"{data['timestamp']}\n"
            )

            f.write(
                f"Status            : "
                f"{data['status']}\n"
            )

            f.write(
                f"Immich Scan       : "
                f"{data['immich_scan']}\n"
            )

            f.write("\n")

            f.write(
                f"Dateien           : "
                f"{data['total']}\n"
            )

            f.write(
                f"Verschoben        : "
                f"{data['moved']}\n"
            )

            f.write(
                f"Ohne Datum        : "
                f"{data['no_date']}\n"
            )

            f.write(
                f"Ziel vorhanden    : "
                f"{data['exists']}\n"
            )

            f.write(
                f"Vorhanden gelöscht: "
                f"{data['exists_deleted']}\n"
            )

            f.write(
                f"Löschfehler       : "
                f"{data['exists_delete_error']}\n"
            )

            f.write(
                f"DRY-RUN           : "
                f"{data['dry_run']}\n"
            )

            f.write(
                f"Ignoriert          : "
                f"{data['ignored']}\n"
            )

            f.write("\n")

            f.write(
                "=" * 72 + "\n"
            )

    # ========================================================
    # HTML
    # ========================================================

    def to_html(self):

        data = self.to_dict()

        status_class = (
            "created"
            if data["status"] == "OK"
            else "error"
        )

        scan_class = (
            "created"
            if data["immich_scan"] == "OK"
            else "error"
        )

        return f"""<!DOCTYPE html>
<html lang="de">

<head>

<meta charset="UTF-8">

<title>Fotoimportbericht</title>

<link
    rel="stylesheet"
    href="/static/style.css"
>

</head>

<body>

<div class="card">

<h2>Fotoimportbericht</h2>

<p>
<b>{data["timestamp"]}</b>
</p>

<hr>

<table>

<tr>

<th>Status</th>
<th>Immich Scan</th>
<th>Dateien</th>
<th>Verschoben</th>
<th>Ohne Datum</th>
<th>Ziel vorhanden</th>
<th>Gelöscht</th>
<th>Löschfehler</th>
<th>Ignoriert</th>

</tr>

<tr>

<td class="{status_class}">
{data["status"]}
</td>

<td class="{scan_class}">
{data["immich_scan"]}
</td>

<td>
{data["total"]}
</td>

<td>
{data["moved"]}
</td>

<td>
{data["no_date"]}
</td>

<td>
{data["exists"]}
</td>

<td>
{data["exists_deleted"]}
</td>

<td>
{data["exists_delete_error"]}
</td>

<td>
{data["ignored"]}
</td>

</tr>

</table>

<hr>

<p>

<a
    class="button"
    href="/"
>
Zur Startseite
</a>

</p>

</div>

</body>

</html>
"""

    # ========================================================
    # HTML SPEICHERN
    # ========================================================

    def save_html(self, filename):

        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                self.to_html()
            )

    # ========================================================
    # BEIDE REPORTS SPEICHERN
    # ========================================================

    def save(self, html_filename, txt_filename):

        self.save_html(
            html_filename
        )

        self.save_txt(
            txt_filename
        )