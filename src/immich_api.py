import requests


class Immich:

    def __init__(self, url, api_key):

        self.url = url.rstrip("/")

        self.headers = {
            "Accept": "application/json",
            "x-api-key": api_key
        }


    def test_connection(self):
        try:
            r = requests.get(
                f"{self.url}/server/version",
                headers=self.headers,
                timeout=5
            )
            return r.status_code == 200
        except requests.RequestException:
            return False


    def get_albums(self):

        r = requests.get(
            self.url + "/albums",
            headers=self.headers,
            timeout=30
        )

        r.raise_for_status()

        return r.json()


    def album_exists(self, name):

        albums = self.get_albums()

        for album in albums:

            if album["albumName"] == name:
                return album

        return None


    def create_album(self, name):

        payload = {
            "albumName": name
        }

        r = requests.post(
            self.url + "/albums",
            headers=self.headers,
            json=payload,
            timeout=30
        )

        r.raise_for_status()

        return r.json()