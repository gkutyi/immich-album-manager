import os
import re
import json

#
# Ordner, die niemals als Album berücksichtigt werden
#

SYSTEM_FOLDERS = {
    ".@__thumb",
    "@Recycle",
    "#recycle",
    ".Trash",
    ".Trashes",
    ".DS_Store",
    "Thumbs.db",
    "iPod Photo Cache",
    "lost+found",
}

#
# Benutzerdefinierte Ausschlüsse
#

DEFAULT_EXCLUDES = {
    "Import",
    "Other",
    "Scan",
    "Unknown Year Taken",
}


def is_system_folder(name: str) -> bool:
    """Versteckte/Systemordner erkennen."""

    if name.startswith("."):
        return True

    return name in SYSTEM_FOLDERS


def is_excluded(name: str, excludes=None) -> bool:

    if excludes is None:
        excludes = DEFAULT_EXCLUDES

    return name in excludes


#
# Jahresordner
#

YEAR_PATTERN = re.compile(r"^(19|20)\d{2}$")


def is_year_folder(name: str) -> bool:
    return YEAR_PATTERN.match(name) is not None


#
# Qfiling-Tagesordner
#

DATE_PATTERNS = [

    re.compile(r"^\d{4}-\d{2}-\d{2}$"),   # 2026-07-22

    re.compile(r"^\d{8}$"),               # 20260722

    re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), # 22.07.2026

]


def is_day_folder(name: str) -> bool:

    for pattern in DATE_PATTERNS:

        if pattern.match(name):

            return True

    return False