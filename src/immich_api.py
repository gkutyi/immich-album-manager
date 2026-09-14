import requests
from asset_cache import AssetCache


class Immich:

    def __init__(self, url, api_key):

        #
        # "/api" am Ende entfernen
        #

        self.base_url = url.rstrip("/")

        self.headers = {

            "x-api-key": api_key,

            "Accept": "application/json",

        }

    # ---------------------------------------------------------

    def test_connection(self):

        r = requests.get(

            f"{self.base_url}/albums",

            headers=self.headers,

            timeout=20,

        )

        return r.status_code == 200

    # ---------------------------------------------------------

    def get_albums(self):

        r = requests.get(

            f"{self.base_url}/albums",

            headers=self.headers,

            timeout=30,

        )

        r.raise_for_status()

        return r.json()

    # ---------------------------------------------------------

    def get_album_lookup(self):
        """
        Dictionary:
            albumname -> Albumobjekt
        """

        lookup = {}

        for album in self.get_albums():

            #
            # verschiedene Immich-Versionen
            #

            name = (

                album.get("albumName")

                or album.get("name")

                or ""

            )

            if name:

                lookup[name.casefold()] = album

        return lookup

    # ---------------------------------------------------------

    def create_album(self, name):

        r = requests.post(

            f"{self.base_url}/albums",

            headers=self.headers,

            json={

                "albumName": name

            },

            timeout=30,

        )

        r.raise_for_status()

        return r.json()

# ---------------------------------------------------------

    def add_assets_to_album(
        self,
        album_id,
        asset_ids
    ):
        """
        Fügt vorhandene Assets einem Album hinzu.

        Es werden ausschließlich Referenzen gesetzt.
        Die Dateien werden NICHT erneut importiert.
        """

        if not asset_ids:
            return

        r = requests.put(

            f"{self.base_url}/albums/{album_id}/assets",

            headers=self.headers,

            json={

                "ids": asset_ids

            },

            timeout=120

        )

        if r.status_code not in (200, 201):

            raise Exception(

                f"Assets konnten nicht zum Album hinzugefügt werden ({r.status_code})"

            )

        return r.json()

    # ---------------------------------------------------------

    def get_all_assets(self):
        """
        Liest alle Assets über
        POST /search/metadata
        """

        assets = []

        page = 1

        while True:

            response = requests.post(

                f"{self.base_url}/search/metadata",

                headers=self.headers,

                json={

                    "page": page,

                    "size": 1000

                },

                timeout=60,

            )

            response.raise_for_status()

            data = response.json()

            #
            # verschiedene Immich-Versionen
            #

            if "assets" in data:

                items = data["assets"]

                if isinstance(items, dict):

                    items = items.get("items", [])

            elif "items" in data:

                items = data["items"]

            else:

                items = []

            if not items:

                break

            assets.extend(items)

            page += 1

        return assets

    # ---------------------------------------------------------

    def get_asset_index(self, force=False):

        #
        # Vorhandenen Cache verwenden
        #

        if not force and AssetCache.exists():

            return AssetCache.get_index()

        #
            # Cache neu aufbauen
        #

        cache = {}

        for asset in self.get_all_assets():

            path = asset.get("originalPath")
            asset_id = asset.get("id")

            if path and asset_id:
                cache[path] = asset_id

        AssetCache.save(cache)

        return cache

    # ---------------------------------------------------------

    def build_asset_cache(self):
        """
        Rückwärtskompatibel zu älteren Commits.
        """

        return self.get_asset_index()

    # ---------------------------------------------------------

    def api_probe(self):

        tests = [

            ("GET", "/assets"),

            ("GET", "/assets/statistics"),

            ("POST", "/search/metadata"),

            ("POST", "/search"),

            ("GET", "/server-info"),

            ("GET", "/server-info/version"),

        ]

        result = []

        for method, path in tests:

            url = self.base_url + path

            try:

                if method == "GET":

                    r = requests.get(
                        url,
                        headers=self.headers,
                        timeout=10
                    )

                else:

                    r = requests.post(
                        url,
                        headers=self.headers,
                        json={},
                        timeout=10
                    )

                result.append({

                    "method": method,

                    "path": path,

                    "status": r.status_code

                })

            except Exception as ex:

                result.append({

                    "method": method,

                    "path": path,

                    "status": str(ex)

                })

        return result

# ---------------------------------------------------------

    def get_album_assets(self, album_id):

        ids = set()

        #
        # 1. Alle Zeit-Buckets des Albums holen
        #
        r = requests.get(
            f"{self.base_url}/timeline/buckets",
            headers=self.headers,
            params={
                "albumId": album_id,
                "order": "desc",
            },
            timeout=60,
        )

        r.raise_for_status()

        buckets = r.json()

        print(f"Album {album_id}: {len(buckets)} Buckets")

        #
        # 2. Jeden Bucket laden
        #
        for bucket in buckets:

            if isinstance(bucket, dict):
                time_bucket = bucket.get("timeBucket")
            else:
                time_bucket = bucket

            r = requests.get(
                f"{self.base_url}/timeline/bucket",
                headers=self.headers,
                params={
                    "albumId": album_id,
                    "order": "desc",
                    "timeBucket": time_bucket,
                },
                timeout=60,
            )

            r.raise_for_status()

            data = r.json()

            #
            # Immich >= v1.135 liefert Timeline-Spaltenformat
            #
            if isinstance(data, dict) and "id" in data:
                asset_ids = data["id"]

                print(f"  {len(asset_ids)} Assets")

                ids.update(asset_ids)

            #
            # ältere Versionen
            #
            elif isinstance(data, list):
                print(f"  {len(data)} Assets")

                for asset in data:
                    ids.add(asset["id"])

            #
            # noch ältere Version
            #
            elif isinstance(data, dict) and "assets" in data:
                assets = data["assets"]

                print(f"  {len(assets)} Assets")

                for asset in assets:
                    ids.add(asset["id"])

            else:
                print("Unbekanntes Antwortformat:")
                print(data)

        print(f"Album enthält {len(ids)} Assets")

        return ids

    def get_asset(self, asset_id):
        """
        Liefert die vollständigen Metadaten eines Immich-Assets.
        """
        r = requests.get(
            f"{self.base_url}/assets/{asset_id}",
            headers=self.headers,
            timeout=30
        )

        if r.status_code != 200:
            raise Exception(
                f"Asset {asset_id} konnte nicht geladen werden: "
               f"{r.status_code} {r.text}"
            )

        return r.json()


    def get_live_photo_video_ids(self, asset_ids):
        """
        Ermittelt jene Asset-IDs, die in Immich als versteckte
        Live-Photo/Motion-Photo-Videos geführt werden.

        Immich verwendet:
          type       = VIDEO
          visibility = hidden

        für den Motion-Anteil eines Live Photos.

        Es werden ausschließlich die übergebenen Asset-IDs geprüft.
        """
        live_photo_video_ids = set()

        for asset_id in asset_ids:
            try:
                asset = self.get_asset(asset_id)

                if (
                    asset.get("type") == "VIDEO"
                    and asset.get("visibility") == "hidden"
                ):
                    live_photo_video_ids.add(asset_id)

            except Exception as e:
                print(
                    f"[WARN] Live-Photo-Prüfung für "
                    f"{asset_id} fehlgeschlagen: {e}"
                )

        return live_photo_video_ids