import os
import logging
import threading
import time
import webbrowser
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, request
from spotipy import SpotifyOAuth, Spotify

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "playlist-read-private playlist-modify-private playlist-modify-public"
TIMEOUT_SECONDS = 60

logger = logging.getLogger("echoseed.auth")

class SpotifyAuthService:
    def __init__(self):
        self.auth_manager = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            open_browser=False,
            show_dialog=True,
            cache_path=Path.home() / ".spotify_cache"
        )
        self.spotify = None
        self.auth_code = None
        self.token_info = None
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
        cached_token = self.auth_manager.get_cached_token()
        if cached_token:
            logger.info("[SpotifyAuthService] Using cached token...")
            self.token_info = cached_token
            self.spotify = Spotify(auth=cached_token["access_token"])
            return

        logger.info("[SpotifyAuthService] No cached token found. Starting browser auth flow...")
        self._do_browser_auth()

    def _do_browser_auth(self):
        """Run browser OAuth flow and save tokens into cache."""
        server_thread = threading.Thread(
            target=lambda: self._app.run(port=8888, debug=False, use_reloader=False)
        )
        server_thread.start()

        auth_url = self.auth_manager.get_authorize_url()
        logger.info(f"[SpotifyAuthService] Opening {auth_url} in your browser...")
        time.sleep(3)
        webbrowser.open(auth_url)

        # Wait for auth code
        start = time.time()
        while not self.auth_code and (time.time() - start) < TIMEOUT_SECONDS:
            time.sleep(1)

        if not self.auth_code:
            logger.error("[SpotifyAuthService] Authentication timed out after %s seconds", TIMEOUT_SECONDS)
            raise RuntimeError("Authentication timed out")

        logger.info("Shutting down server thread... (manual kill needed for Flask)")

        self.token_info = self.auth_manager.get_access_token(self.auth_code)
        self.spotify = Spotify(auth=self.token_info["access_token"])
        logger.info("[SpotifyAuthService] Access + Refresh token obtained and cached.")

    def refresh_access_token(self):
        """Force a refresh if you want to."""
        if not self.token_info:
            raise RuntimeError("No token info available, call authenticate() first.")
        refresh_token = self.token_info.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("No refresh token found.")
        self.token_info = self.auth_manager.refresh_access_token(refresh_token)
        self.spotify = Spotify(auth=self.token_info["access_token"])
        logger.info("[SpotifyAuthService] Access token refreshed.")

    def get_spotify_client(self) -> Spotify:
        return self.spotify

    def get_access_token(self):
        return self.token_info["access_token"]

    def get_refresh_token(self):
        return self.token_info.get("refresh_token")
