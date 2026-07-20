import os


class Scanner:

    IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif",
        ".bmp", ".tif", ".tiff",
        ".webp", ".heic", ".heif",
        ".dng", ".cr2", ".cr3",
        ".nef", ".arw", ".rw2", ".orf"
    }

    VIDEO_EXTENSIONS = {
        ".mp4", ".mov", ".avi",
        ".mkv", ".mts", ".m2ts",
        ".wmv", ".mpg", ".mpeg",
        ".3gp"
    }

    IGNORE_DIRS = {
        ".@__thumb",
        "@eaDir",
        "@Recycle",
        "@Recently-Snapshot",
        "iPod Photo Cache"
    }

    def scan(self, roots):

        folders = []

        for root in roots:

            base = root["path"]

            if not os.path.isdir(base):
                continue

            for name in sorted(os.listdir(base)):

                if name in self.IGNORE_DIRS:
                    continue

                full = os.path.join(base, name)

                if not os.path.isdir(full):
                    continue

                images, videos = self.count_media(full)

                folders.append({
                    "name": name,
                    "path": full,
                    "images": images,
                    "videos": videos,
                    "total": images + videos
                })

        return folders

    def count_media(self, folder):

        images = 0
        videos = 0

        for root, dirs, files in os.walk(folder):

            # QNAP-Systemordner ignorieren
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:

                ext = os.path.splitext(file)[1].lower()

                if ext in self.IMAGE_EXTENSIONS:
                    images += 1

                elif ext in self.VIDEO_EXTENSIONS:
                    videos += 1

        return images, videos