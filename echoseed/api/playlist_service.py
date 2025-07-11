import logging
import time
from typing import List
from spotipy import Spotify
from spotipy.exceptions import SpotifyException

from echoseed.model.track import Track
from echoseed.model.playlist import Playlist

logger = logging.getLogger(__name__)

class SpotifyPlaylistService:
    def __init__(self, spotify_client: Spotify):
        self.spotify = spotify_client
        logger.info("Initialized SpotifyPlaylistService")

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
