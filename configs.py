import requests
import json
import base64
import os
from dotenv import load_dotenv

# ----------------------------------------------------------------------

load_dotenv()

class Configs:
    def __init__(self):
        self.CONSUMER_KEY = os.getenv("CONSUMER_KEY")
        self.CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
        self.BASE_URL = os.getenv("BASE_URL", "https://api.princeton.edu:443/active-directory/1.0.6")
        self.USERS_BASIC = "/users/basic"
        self.REFRESH_TOKEN_URL="https://api.princeton.edu:443/token"
        self._refreshToken(grant_type="client_credentials")

    def _refreshToken(self, **kwargs):
        req = requests.post(
            self.REFRESH_TOKEN_URL, 
            data=kwargs, 
            headers={
                "Authorization": "Basic " + base64.b64encode(bytes(self.CONSUMER_KEY + ":" + self.CONSUMER_SECRET, "utf-8")).decode("utf-8")
            },
        )
        text = req.text
        response = json.loads(text)
        self.ACCESS_TOKEN = response["access_token"]