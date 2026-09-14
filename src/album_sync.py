import os

from asset_cache import AssetCache

class AlbumSync:



    def __init__(self, api, report=None):

        self.api = api

        self.report = report

        #
        # wird später für die Assets verwendet
        #

        self.asset_cache = None

    def compare(self, albums):

        #
        # Alle Immich-Alben laden
        #

        immich_albums = self.api.get_albums()

        #
        # Nach dem tatsächlichen Album-Namen indizieren
        #

        existing = {}

        for album in immich_albums:

            name = album.get(
                "albumName",
                ""
            ).strip().lower()

            if name:
                existing[name] = album

        #
        # Scanner-Ergebnis ergänzen
        #

        for album in albums:

            #
            # Tatsächlichen Immich-Namen erzeugen
            #
            # Beispiel:
            # album = "Import"
            # year  = "2018"
            #
            # => "Import (2018)"
            #

            if album.get("year"):

                album_name = (
                    f"{album['album']} ({album['year']})"
                )

            else:

                album_name = album["album"]

            key = album_name.strip().lower()

            #
            # Regel
            #

            rule = album.get(
                "rule",
                {}
            )

            auto_add = rule.get(
                "auto_add",
                False
            )

            #
            # Existiert das Album bereits?
            #

            if key in existing:

                album["exists"] = True
                album["create"] = False

                album["immich_id"] = existing[key]["id"]

                #
                # Assets des bestehenden Albums laden
                #

                immich_assets = self.api.get_album_assets(album["immich_id"])

                local_assets = set(album.get("asset_ids", []))

                # Assets, die lokal vorhanden sind, aber laut Timeline-Abfrage
                # nicht im Immich-Album gefunden wurden.
                missing_ids = list(local_assets - immich_assets)

                # Immich führt den Motion-Anteil von Live Photos als
                # VIDEO + visibility=hidden. Diese Assets werden absichtlich
                # nicht von get_album_assets() zurückgeliefert.
                #
                # Sie dürfen daher nicht als fehlende Album-Assets gewertet werden.
                live_photo_video_ids = self.api.get_live_photo_video_ids(missing_ids)

                if live_photo_video_ids:
                    print(
                        f"[INFO] {album_name}: "
                        f"{len(live_photo_video_ids)} Live-Photo-Motion-Assets "
                        f"aus missing entfernt"
                    )

                missing_ids = [
                    asset_id
                    for asset_id in missing_ids
                    if asset_id not in live_photo_video_ids
                ]

                album["missing_ids"] = missing_ids
                album["missing"] = len(missing_ids)
                album["live_photo_video_ids"] = list(live_photo_video_ids)

                album["update"] = (
                    auto_add and len(missing_ids) > 0
                )

            else:

                #
                # Album existiert noch nicht
                #

                album["exists"] = False
                album["create"] = True
                album["update"] = False

                album["immich_id"] = None

                album["missing_ids"] = []
                album["missing"] = 0

        return albums

    def update_existing_albums(self, albums):
        """
        Ergänzt bestehende Alben um fehlende Assets.
        """

        updated = 0
        added_assets = 0

        for album in albums:

            #
            # Automatische Ergänzung deaktiviert?
            #

            if not album["rule"].get("auto_add", False):

                print(
                    f"{album['album']}: automatische Ergänzung deaktiviert"
                )

                if self.report:

                    self.report.add_skipped(
                        album["album"],
                        "automatische Ergänzung deaktiviert"
                    )

                continue

            if not album["exists"]:
                continue

            missing = album.get("missing_ids", [])

            # Sicherheitsfilter: Live-Photo-Motion-Assets niemals
            # als normale fehlende Album-Assets hinzufügen.
            live_photo_video_ids = set(
                album.get("live_photo_video_ids", [])
            )

            missing = [
                asset_id
                for asset_id in missing
                if asset_id not in live_photo_video_ids
            ]

            if not missing:

                print(
                    f"{album['album']}: bereits vollständig"
                )

                continue

            print("=" * 80)
            print("Album:", album["album"])
            print("fehlende Assets:", len(missing))

            print("Erste fehlende IDs:")

            for asset_id in missing[:10]:

                print(asset_id)

            print(
                f"Insgesamt {len(missing)} Assets werden hinzugefügt."
            )

            print(
                f"{album['album']}: "
                f"{len(missing)} neue Assets",
                flush=True
            )

            try:

                self.api.add_assets_to_album(
                    album["immich_id"],
                    missing
                )

                added_assets += len(missing)

                if self.report:

                    self.report.add_updated(
                        album["album"],
                        len(missing)
                    )

                album["missing"] = 0
                album["missing_ids"] = []
                album["update"] = False

                updated += 1

            except Exception as ex:

                print(
                    f"Fehler beim Aktualisieren von "
                    f"{album['album']}: {ex}"
                )

                if self.report:

                    self.report.add_error(
                        album["album"],
                        ex
                    )

        print(
            f"Insgesamt {added_assets} Assets hinzugefügt."
        )

        return updated


    def create_missing_albums(self, albums):
        """
        Legt alle fehlenden Alben in Immich an
        und fügt sofort alle bereits vorhandenen
        Assets aus dem Cache hinzu.
        """

        created = 0

        for album in albums:

            #
            # Automatische Aktualisierung erlaubt?
            #

            if not album.get("rule", {}).get("auto_add", False):
                print(
                    f"[SKIP] Album '{album['album']}' "
                    f"auto_add=False"
                )
                continue

            if not album["create"]:
                continue

            #
            # Albumname zusammensetzen
            #

            if album["year"]:

                album_name = (
                    f"{album['album']} ({album['year']})"
                )

            else:

                album_name = album["album"]

            print(f"Erstelle Album: {album_name}")

            try:

                result = self.api.create_album(
                    album_name
                )

                album["immich_id"] = result.get("id")

                if not album["immich_id"]:

                    raise Exception(
                        f"Immich hat keine Album-ID zurückgegeben.\n"
                        f"Antwort: {result}"
                    )

                #
                # Bereits vorhandene Assets im Album ermitteln
                #

                existing = self.api.get_album_assets(
                    album["immich_id"]
                )

                #
                # Nur fehlende Assets hinzufügen
                #

                missing = [

                    asset_id

                    for asset_id in album.get("asset_ids", [])

                    if asset_id not in existing

                ]

                added = 0

                if missing:

                    print(
                        f"{album_name}: {len(missing)} neue Assets"
                    )

                    self.api.add_assets_to_album(

                        album["immich_id"],

                        missing

                    )

                    added = len(missing)

                else:

                    print(
                        f"{album_name}: bereits vollständig"
                    )

                #
                # Report
                #

                if self.report:

                    self.report.add_created(
                        album_name,
                        added
                    )

                #
                # Status aktualisieren
                #

                album["exists"] = True
                album["create"] = False
                album["update"] = False

                created += 1

            except Exception as ex:

                print(
                    f"Fehler beim Erstellen von "
                    f"{album_name}: {ex}"
                )

                if self.report:

                    self.report.add_error(
                        album_name,
                        ex
                    )

        return created


    def prepare_assets(self, albums):

        """
        Ergänzt jedes Album um die vorhandenen Immich Asset-IDs.
        """

        for album in albums:

            self.collect_asset_ids(album)

        return albums

    def collect_asset_ids(self, album):

        """
        Ermittelt Asset-IDs anhand des Asset-Caches.
        """

        cache = AssetCache.get_index()

        asset_ids = []


        for root, dirs, files in os.walk(album["path"]):

            #
            # versteckte Ordner ignorieren
            #

            dirs[:] = [

                d for d in dirs
                if not d.startswith(".")

            ]


            for file in files:

                full = os.path.join(
                    root,
                    file
                )


                asset_id = cache.get(full)


                if asset_id:

                    asset_ids.append(asset_id)


        album["asset_ids"] = asset_ids

        album["asset_count"] = len(asset_ids)


        return album