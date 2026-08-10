import json
import os
import copy

CACHE_FILE = "/config/asset_index.json"

CONFIG_FILE = "/config/settings.json"

DEFAULT_CONFIG = {
    "library_root": "/external",

    "immich": {
        "url": "http://immich_server:2283/api",
        "api_key": ""
    },
    "cache":{

        "auto_rebuild":False

    },

    "album_roots": []
}


class Config:

    @staticmethod
    def load():

        if not os.path.exists(CONFIG_FILE):
            return copy.deepcopy(DEFAULT_CONFIG)

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        return Config.migrate(cfg)

    @staticmethod
    def save(cfg):

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)

    @staticmethod
    def migrate(cfg):
        """
        Unterstützt alte Versionen der settings.json
        """

        #
        # Alte Felder übernehmen
        #

        if "immich_url" in cfg:

            cfg["immich"] = {
                "url": cfg.pop("immich_url"),
                "api_key": cfg.pop("api_key", "")
            }

        if "library" in cfg:
            cfg["library_root"] = cfg.pop("library")

        #
        # Defaults ergänzen
        #

        for key, value in DEFAULT_CONFIG.items():
            if key not in cfg:
                cfg[key] = value

        if "immich" not in cfg:
            cfg["immich"] = DEFAULT_CONFIG["immich"].copy()

        if "album_roots" not in cfg:
            cfg["album_roots"] = []
        
        if "cache" not in cfg:

            cfg["cache"] = DEFAULT_CONFIG["cache"].copy()

        return cfg