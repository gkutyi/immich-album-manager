import json
import os
import datetime

CACHE_FILE = "/config/asset_index.json"


class AssetCache:

    @staticmethod
    def exists():

        return os.path.exists(CACHE_FILE)

    @staticmethod
    def load():

        if not os.path.exists(CACHE_FILE):
            return {}

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            #
            # alte Cache-Dateien unterstützen
            #

            if "index" in data:
                return data

            return {

                "created": None,

                "assets": len(data),

                "index": data

            }

    @staticmethod
    def save(cache):

        data = {

            "created": __import__("datetime").datetime.now().isoformat(),

            "assets": len(cache),

            "index": cache

        }

        os.makedirs(
            os.path.dirname(CACHE_FILE),
            exist_ok=True
        )

        with open(
            CACHE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )

    @staticmethod
    def remove():

        if os.path.exists(CACHE_FILE):

            os.remove(CACHE_FILE)
            
    @staticmethod
    def get_index():

        return AssetCache.load()["index"]

        
    @staticmethod
    def info():

        if not os.path.exists(CACHE_FILE):

            return {
                "exists": False,
                "assets": 0,
                "created": "",
                "size": ""
            }

        stat = os.stat(CACHE_FILE)

        data = AssetCache.load()

        created = data.get("created", "")

        #
        # ISO -> europäisches Format
        #

        if created:

            try:

                created = datetime.datetime.fromisoformat(
                    created
                ).strftime("%d.%m.%Y %H:%M")

            except Exception:

                pass

        #
        # Dateigröße
        #

        size = stat.st_size

        if size > 1024 * 1024:

            size = f"{size/(1024*1024):.1f} MB"

        elif size > 1024:

            size = f"{size/1024:.1f} kB"

        else:

            size = f"{size} Byte"

        return {

            "exists": True,

            "assets": data.get("assets", 0),

            "created": created,

            "size": size

        }