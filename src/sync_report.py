import os

from datetime import datetime


class SyncReport:

    def __init__(self):

        self.created = []
        self.updated = []
        self.skipped = []
        self.errors = []

    def add_created(self, album, assets):

        self.created.append({
            "album": album,
            "assets": assets
        })

    def add_updated(self, album, assets):

        self.updated.append({
            "album": album,
            "assets": assets
        })

    def add_skipped(self, album, reason):

        self.skipped.append({
            "album": album,
            "reason": reason
        })

    def add_error(self, album, error):

        self.errors.append({
            "album": album,
            "error": str(error)
        })

    def save(self, filename):

        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        with open(filename, "w", encoding="utf-8") as f:

            f.write("=" * 72 + "\n")
            f.write("Immich Album Manager - Synchronisationsbericht\n")
            f.write("=" * 72 + "\n\n")

            f.write(
                datetime.now().strftime(
                    "%d.%m.%Y %H:%M:%S"
                )
            )

            f.write("\n\n")

            #
            # Neue Alben
            #

            f.write("NEUE ALBEN\n")
            f.write("-" * 72 + "\n")

            if self.created:

                for album in self.created:

                    f.write(
                        f"{album['album']} "
                        f"({album['assets']} Assets)\n"
                    )

            else:

                f.write("keine\n")

            f.write("\n")

            #
            # Aktualisierte Alben
            #

            f.write("AKTUALISIERTE ALBEN\n")
            f.write("-" * 72 + "\n")

            if self.updated:

                for album in self.updated:

                    f.write(
                        f"{album['album']} "
                        f"(+{album['assets']} Assets)\n"
                    )

            else:

                f.write("keine\n")

            f.write("\n")

            #
            # Übersprungene Alben
            #

            f.write("ÜBERSPRUNGEN\n")
            f.write("-" * 72 + "\n")

            if self.skipped:

                for album in self.skipped:

                    f.write(
                        f"{album['album']} : "
                        f"{album['reason']}\n"
                    )

            else:

                f.write("keine\n")

            f.write("\n")

            #
            # Fehler
            #

            f.write("FEHLER\n")
            f.write("-" * 72 + "\n")

            if self.errors:

                for album in self.errors:

                    f.write(
                        f"{album['album']} : "
                        f"{album['error']}\n"
                    )

            else:

                f.write("keine\n")

            f.write("\n")
            f.write("=" * 72 + "\n")

            f.write(
                f"Neue Alben        : {len(self.created)}\n"
            )

            f.write(
                f"Aktualisiert      : {len(self.updated)}\n"
            )

            f.write(
                f"Übersprungen      : {len(self.skipped)}\n"
            )

            f.write(
                f"Fehler            : {len(self.errors)}\n"
            )
            
    def to_dict(self):

        return {

            "created": self.created,

            "updated": self.updated,

            "skipped": self.skipped,

            "errors": self.errors,

            "created_count": len(self.created),

            "updated_count": len(self.updated),

            "skipped_count": len(self.skipped),

            "error_count": len(self.errors),

            "timestamp": datetime.now().strftime(
                "%d.%m.%Y %H:%M:%S"
            )

        }