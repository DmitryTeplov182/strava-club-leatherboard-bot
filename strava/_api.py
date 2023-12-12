import requests


class InfoStravaClub:
    """Get information about the Strava Club"""

    auth_url = "https://www.strava.com/oauth/token"

    def __init__(self, club_id):
        self.club_id = club_id
        self.club_url = "https://www.strava.com/api/v3/clubs/" + str(
            self.club_id
        )
        self.headers = {"Authorization": "Bearer " + self.access_token}
        self.params = {"per_page": 200, "page": 1}

    @property
    def access_token(self):
        """Get access token"""
        payload = {
            "client_id": "***",
            "client_secret": "***",
            "refresh_token": "***",
            "grant_type": "refresh_token",
            "f": "json",
        }
        res = requests.post(self.auth_url, data=payload, timeout=5)
        access_token = res.json()["access_token"]
        return access_token

    @property
    def get_club_info(self):
        """Get club info"""
        response = requests.get(self.club_url, headers=self.headers, timeout=5)
        return response.json()
