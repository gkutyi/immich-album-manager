import os

from rules import (
    is_system_folder,
    is_excluded,
    is_year_folder,
    is_day_folder,
)
                    
from album_rules import AlbumRules

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
    ".webp",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".mts",
    ".m2ts",
    ".3gp",
    ".wmv",
}


class AlbumScanner:

    def __init__(self, excludes=None):

        self.excludes = excludes or []

        self.albums = []
        
        #
        # Asset-Cache
        #

        self.asset_index = {}
        
    def set_asset_index(self, index):
        """
        Übergibt den geladenen Asset-Cache.
    
        index:
            originalPath -> Asset-ID
        """

        self.asset_index = index or {}
        
    def scan(self, roots):

        self.albums = []

        for root in roots:

            if not root.get("enabled", True):
                continue

            path = root["path"]

            if not os.path.isdir(path):
                continue

            self.scan_root(path)

        return self.albums
        
    def scan_root(self, root):

        for entry in sorted(os.listdir(root)):

            if is_system_folder(entry):
                continue

            if is_excluded(entry, self.excludes):
                continue

            full = os.path.join(root, entry)

            if not os.path.isdir(full):
                continue

            #
            # Jahresordner?
            #

            if is_year_folder(entry):

                self.scan_year(root, full, entry)

            else:

                self.add_album(
                    album=entry,
                    path=full,
                    year=None,
                    mode="DIRECT",
                )

    def scan_year(self, root, year_path, year):

        for entry in sorted(os.listdir(year_path)):

            if is_system_folder(entry):
                continue

            if is_day_folder(entry):
                continue

            full = os.path.join(year_path, entry)

            if not os.path.isdir(full):
                continue

            self.add_album(
                album=entry,
                path=full,
                year=year,
                mode="YEAR",
            )
            
    def add_album(
        self,
        album,
        path,
        year,
        mode,
    ):

        images = 0
        videos = 0
        asset_ids = []
        cache_hits = 0
        cache_misses = 0

        for root, dirs, files in os.walk(path):

            #
            # Systemordner überspringen
            #

            dirs[:] = [
                d
                for d in dirs
                if not is_system_folder(d)
            ]

            for file in files:

                ext = os.path.splitext(file)[1].lower()

                #
                # Nur echte Assets berücksichtigen
                #
                if ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)

                asset_id = self.asset_index.get(full_path)

                if asset_id:
                    asset_ids.append(asset_id)
                    cache_hits += 1
                else:
                    cache_misses += 1

                if ext in IMAGE_EXTENSIONS:
                    images += 1
                else:
                    videos += 1
        
        #
        # Regel für dieses Album laden
        #
        
        rule = AlbumRules.get(album)
                    
        self.albums.append({

            "album": album,

            "year": year,

            "mode": mode,

            "path": path,

            "images": images,

            "videos": videos,

            "total": images + videos,

            #
            # wird später von album_sync.py ergänzt
            #

            "exists": False,

            "create": True,

            "update": False,

            "asset_ids": asset_ids,

            "cache_hits": cache_hits,

            "cache_misses": cache_misses,
            
            "rule": rule,

        })