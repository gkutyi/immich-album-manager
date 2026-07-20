import json
import os

CONFIG_FILE = "/config/settings.json"


DEFAULT_CONFIG = {
    "library_root": "/external",

    "immich": {
        "url": "http://immich_server:2283/api",
        "api_key": ""
    },

    "album_roots": []
}


class Config:

    @staticmethod
    def load():

        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_CONFIG

        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)

        return Config.migrate(cfg)

    @staticmethod
    def save(cfg):

        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)

    @staticmethod
    def migrate(cfg):

        #
        # alte Version unterstützen
        #

        if "immich_url" in cfg:

            cfg["immich"] = {
                "url": cfg.pop("immich_url"),
                "api_key": cfg.pop("api_key")
            }

        if "library" in cfg:

            cfg["library_root"] = cfg.pop("library")

        #
        # Defaults ergänzen
        #

        for key, value in DEFAULT_CONFIG.items():

            if key not in cfg:
                cfg[key] = value

        return cfg