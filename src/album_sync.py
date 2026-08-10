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
        # Nach Namen indizieren
        #

        existing = {}

        for album in immich_albums:

            name = album.get("albumName", "").strip().lower()

            if name:
                existing[name] = album

        #
        # Scanner-Ergebnis ergänzen
        #

        for album in albums:
            
            if not album.get("auto_update", True):

                album["update"] = False
                album["missing"] = 0
                album["missing_ids"] = []

                continue

            key = album["album"].strip().lower()

            if key in existing:

                album["exists"] = True
                album["create"] = False
                album["update"] = False

                #
                # Für spätere Synchronisation merken
                #

                album["immich_id"] = existing[key]["id"]
                
                #
                # Fehlende Assets im Album bestimmen
                #

                immich_assets = self.api.get_album_assets(
                    album["immich_id"]
                )

                local_assets = set(
                    album.get("asset_ids", [])
                )

                missing_ids = list(
                    local_assets - immich_assets
                )

                album["missing_ids"] = missing_ids
                album["missing"] = len(missing_ids)

                rule = album.get("rule", {})

                album["update"] = (
                    album["rule"].get("auto_add", True)
                    and
                    len(missing_ids) > 0
                )

            else:

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
    
            if not album["rule"].get("auto_add", True):

                print(

                    f"{album['album']}: automatische Ergänzung deaktiviert"

                )

                continue

            if not album["exists"]:
                continue

            missing = album.get("missing_ids", [])
            
            added_assets += len(missing)

            if not missing:
                print(f"{album['album']}: bereits vollständig")
                continue

            print("=" * 80)
            print("Album:", album["album"])
            print("fehlende Assets:", len(missing))

            print("Erste fehlende IDs:")

            for asset_id in missing[:10]:
                print(asset_id)
                
            print(f"Insgesamt {added_assets} Assets hinzugefügt.")

            print(
                f"{album['album']}: {len(missing)} neue Assets",
                flush=True
            )

            self.api.add_assets_to_album(
                album["immich_id"],
                missing
            )
            
            if self.report:
                self.report.assets_added(
                    album["album"],
                    len(missing)
                )

            album["missing"] = 0
            album["missing_ids"] = []
            album["update"] = False

            updated += 1

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
            # automatische Aktualisierung erlaubt?
            #

            if not album.get("auto_update", True):

                print(
                    f"{album['album']}: automatische Aktualisierung deaktiviert"
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
                
                if self.report:
                    self.report.album_created(album_name)

            result = self.api.create_album(
                album_name
            )

            album["immich_id"] = result.get("id")

            if not album["immich_id"]:

                raise Exception(
                    f"Immich hat keine Album-ID zurückgegeben.\nAntwort: {result}"
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

            if missing:

                print(
                    f"{album_name}: {len(missing)} neue Assets"
                )

                try:

                    self.api.add_assets_to_album(

                        album["immich_id"],

                        missing

                    )
                    
                    if self.report:
                        self.report.assets_added(
                            album_name,
                            len(missing)
                        )

                except Exception as ex:

                    print(
                        f"Fehler beim Befüllen von "
                        f"{album_name}: {ex}"
                    )
                    
                    if self.report:
                        self.report.error(str(ex))

            else:

                print(
                    f"{album_name}: bereits vollständig"
                )
                
                self.report.album_skipped(album["album"])

            #
            # Status aktualisieren
            #
    
            album["exists"] = True
            album["create"] = False
            album["update"] = False

            created += 1

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