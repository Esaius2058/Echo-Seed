import logging
import time
import random
from typing import List
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from echoseed.api.auth import SpotifyAuthService

from echoseed.model.track import Track
from echoseed.model.playlist import Playlist

logger = logging.getLogger(__name__)

class SpotifyPlaylistService:
    def __init__(self, spotify_client: Spotify):
        self.spotify = spotify_client
        self.user_id = self.spotify.me()["id"]
        logger.info("Initialized SpotifyPlaylistService")

    def get_playlist_id(self, playlist_name):
        if not self.user_id:
           logger.error("No User Id passed in")

        results = self.spotify.user_playlists(self.user_id)
        while results:
            for playlist in results["items"]:
                if playlist["name"].lower() == playlist_name.lower():
                    print(f"Found playlist '{playlist_name}' (ID: {playlist['id']})")
                    return playlist["id"]

            if results["next"]:
                results = self.spotify.next(results)
            else:
                results = None

            print(f"⚠️ Playlist '{playlist_name}' not found.")
            return None

    def get_user_playlists(self) -> List[Playlist]:
        playlists = []
        offset = 0
        limit = 50

        try:
            while True:
                response = self.spotify.current_user_playlists(limit=limit, offset=offset)
                items = response.get("items", [])
                if not items:
                    break

                for item in items:
                    playlist = Playlist(
                        id=item["id"],
                        name=item["name"],
                        owner_id=item["owner"]["id"] if item.get("owner") else "unknown"
                    )
                    if playlist.name:
                        playlists.append(playlist)

                if not response.get("next"):
                    break
                offset += limit

            logger.info("Fetched %d playlists for user.", len(playlists))
            return playlists

        except SpotifyException as e:
            logger.error("Failed to fetch playlists: %s", str(e))
            raise RuntimeError("Playlist fetch failed") from e

    def get_playlist_tracks(self, playlist_id: str) -> List[Track]:
        tracks = []
        offset = 0
        limit = 100

        try:
            while True:
                response = self.spotify.playlist_items(playlist_id, limit=limit, offset=offset)
                items = response.get("items", [])
                if not items:
                    break

                for item in items:
                    track_info = item["track"]
                    track = Track(
                        id=track_info["id"],
                        name=track_info["name"],
                        artist=track_info["artists"][0]["name"]
                    )
                    tracks.append(track)

                logger.info("Fetched %d tracks for playlist %s", len(items), playlist_id)
                if not response.get("next"):
                    break
                offset += limit
                time.sleep(0.2)

            return tracks

        except SpotifyException as e:
            logger.error("Failed to fetch tracks for playlist %s: %s", playlist_id, str(e))
            raise RuntimeError("Track fetch failed") from e

    def randomize_playlist(self, playlist_name: str):
        playlist_id = self.get_playlist_id(playlist_name)
        if not playlist_id:
            logger.warning("⚠️ Playlist '%s' not found.", playlist_name)
            return

        track_uris = []
        tracks = self.spotify.playlist_items(playlist_id, limit=100)
        while tracks:
            for item in tracks["items"]:
                track = item["track"]
                if track:
                    track_uris.append(track["uri"])

            if tracks["next"]:
                tracks = self.spotify.next(tracks)
            else:
                tracks = None

        if not track_uris:
            print("⚠️ No tracks found in playlist.")
            return

        print(f"Fetched {len(track_uris)} tracks from playlist.")

        random.shuffle(track_uris)

        self.spotify.playlist_replace_items(playlist_id, [])
        logger.info("Cleared %s", playlist_name)

        logger.info("Preparing to add %d tracks back", len(track_uris))
        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i + 100]
            self.spotify.playlist_add_items(playlist_id, chunk)
            print(f"Added {len(chunk)} tracks...")

        print("Playlist randomized successfully!")

if __name__ == "__main__":
    auth_service = SpotifyAuthService()
    auth_service.authenticate()
    sp_client =  auth_service.get_spotify_client()
    playlist_service = SpotifyPlaylistService(sp_client)
    playlist_service.randomize_playlist("Slow Drift")