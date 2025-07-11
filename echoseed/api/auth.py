import os
import logging
import threading
import time
import webbrowser
from dotenv import load_dotenv
from flask import Flask, request
from spotipy import SpotifyOAuth, Spotify

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public"
TIMEOUT_SECONDS = 60

logger = logging.getLogger("echoseed.auth")
logging.basicConfig(level=logging.INFO)

class SpotifyAuthService:
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=False,
            show_dialog=True,
            cache_path=".cache"  # Optional: Save tokens
        )
        self.spotify = None
        self.auth_code = None
        self._app = Flask(__name__)
        self._app.add_url_rule('/callback', view_func=self._callback, methods=['GET'])

    def _callback(self):
        self.auth_code = request.args.get("code")
        if self.auth_code:
            logger.info("Received authorization code: %s", self.auth_code)
            return "Authentication successful! You can close this window."
        else:
            logger.error("No authorization code received")
            return "Authentication failed."

    def authenticate(self):
        logger.info("Starting Flask server for OAuth callback...")
        server_thread = threading.Thread(target=lambda: self._app.run(port=8888, debug=False, use_reloader=False))
        server_thread.start()

        auth_url = self.auth_manager.get_authorize_url()
        logger.info("Open this URL in your browser: %s", auth_url)
        webbrowser.open(auth_url)

        # Wait for auth code
        start = time.time()
        while not self.auth_code and (time.time() - start) < TIMEOUT_SECONDS:
            time.sleep(1)

        if not self.auth_code:
            logger.error("Authentication timed out after %s seconds", TIMEOUT_SECONDS)
            raise RuntimeError("Authentication timed out")

        logger.info("Shutting down server thread...")
        # Note: Flask server won't stop automatically — you can kill it if needed

        token_info = self.auth_manager.get_access_token(self.auth_code)
        self.spotify = Spotify(auth=token_info["access_token"])
        logger.info("Access token obtained.")

    def get_spotify_client(self) -> Spotify:
        return self.spotify