import json
import os
import random
import logging
from pathlib import Path
from dotenv import load_dotenv
from spotipy import Spotify
from openai import OpenAI
from config.logger_config import setup_logger

load_dotenv()
setup_logger()
logger = logging.getLogger("echoseed.playlist_generator")

base_dir = Path(__file__).resolve().parents[2]
clustered_tracks_file = base_dir / "echoseed" / "data" / "processed" / "clustered_tracks.csv"
mood_labels_file = base_dir / "cluster_mood_map.json"


class PlaylistGenerator:
    def __init__(self, spotify_client: Spotify, mood):
        logger.info("[PlaylistGenerator] Initializing with mood: %s", mood)
        self.spotify = spotify_client
        self.user = self.spotify.me()
        logger.info("[PlaylistGenerator] Authenticated user: %s", self.user.get("id"))
        self.mood = mood

        self.ai_client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        logger.info("[PlaylistGenerator] Loading clustered tracks from %s", clustered_tracks_file)
        with open(clustered_tracks_file, "r") as f:
            self.clustered_tracks = f.read()

        logger.info("[PlaylistGenerator] Loading mood labels from %s", mood_labels_file)
        with open(mood_labels_file, "r") as f:
            self.mood_labels = json.load(f)

    def get_clusters_for_mood(self) -> list:
        logger.info("[PlaylistGenerator] Finding clusters for mood: %s", self.mood)
        matching_clusters = []
        for cluster_id, label in self.mood_labels.items():
            logger.debug("Cluster %s -> %s", cluster_id, label)
            if label == self.mood:
                matching_clusters.append(cluster_id)

        logger.info("[PlaylistGenerator] Found %d matching clusters", len(matching_clusters))
        return matching_clusters

    def get_playlist_name(self) -> str:
        logger.info("[PlaylistGenerator] Generating playlist name for mood: %s", self.mood)
        response = self.ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "You are a creative playlist name generator."},
                {
                    "role": "user",
                    "content": (
                        f"Give me 5 unique, catchy playlist names for the mood '{self.mood}'. "
                        "Keep names short (1–4 words). "
                        "Do not include the word 'playlist'. "
                        "Output only the list of names, nothing else."
                    )
                }
            ]
        )

        names_text = response.choices[0].message.content.strip()
        names = [line.strip("-•0123456789 ").strip() for line in names_text.splitlines() if line.strip()]
        logger.info("[PlaylistGenerator] Candidate names: %s", names)

        chosen_name = random.choice(names) if names else "Untitled Mix"
        logger.info("[PlaylistGenerator] Selected playlist name: %s", chosen_name)
        return chosen_name

    def get_artists_from_playlists(self):
        logger.info("[PlaylistGenerator] Collecting artists from user playlists")
        artists = set()
        playlists = self.spotify.user_playlists(self.user["id"], limit=10)

        for playlist in playlists["items"]:
            logger.debug("[PlaylistGenerator] Checking playlist: %s", playlist["name"])
            playlist_id = playlist["id"]
            tracks = self.spotify.playlist_items(playlist_id)

            while tracks:
                for item in tracks["items"]:
                    track = item["track"]
                    if track:
                        for artist in track["artists"]:
                            artists.add(artist["name"])

                if tracks["next"]:
                    tracks = self.spotify.next(tracks)
                else:
                    tracks = None

        logger.info("[PlaylistGenerator] Found %d unique artists", len(artists))
        return list(artists)

    def get_recommended_tracks(self, limit: int = 25):
        logger.info("[PlaylistGenerator] Requesting %d recommended tracks for mood: %s", limit, self.mood)
        artists = self.get_artists_from_playlists()
        logger.debug("[PlaylistGenerator] Artist pool: %s", artists)

        prompt = (
            f"I have a list of artists: {', '.join(artists)}.\n"
            f"The desired mood is '{self.mood}'.\n"
            f"Based on their style, sound, and the given mood, recommend {limit} songs "
            f"(across any artists, including but not limited to these).\n"
            f"The songs should match the mood and flow together as a cohesive playlist.\n"
            f"Return only the song title and artist in a clean numbered list."
        )

        response = self.ai_client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": "You are a music recommendation engine."},
                {"role": "user", "content": prompt}
            ],
        )

        recommendation_text = response.choices[0].message.content.strip()
        recommendations = [
            line.strip("-•0123456789. ").strip()
            for line in recommendation_text.splitlines()
            if line.strip()
        ]

        logger.info("[PlaylistGenerator] Got %d recommendations", len(recommendations))
        return recommendations[:limit]

    def generate_playlist(self, limit: int = 25):
        logger.info("[PlaylistGenerator] Creating a new playlist for mood: %s", self.mood)
        playlist_name = self.get_playlist_name()
        playlist = self.spotify.user_playlist_create(self.user["id"], playlist_name)
        logger.info("[PlaylistGenerator] Created playlist: %s (%s)", playlist_name, playlist["id"])

        track_uris = []
        recommended_tracks = self.get_recommended_tracks()
        for recommended_track in recommended_tracks:
            logger.debug("[PlaylistGenerator] Searching for track: %s", recommended_track)
            parts = recommended_track.split(" - ")
            if len(parts) == 2:
                name, artist = parts
            else:
                name, artist = recommended_track, ""

            query = f"{name} {artist}".strip()
            results = self.spotify.search(q=query, type="track", limit=1)

            items = results.get("tracks", {}).get("items", [])
            if items:
                track_uri = items[0]["uri"]
                logger.debug("[PlaylistGenerator] Found track URI: %s", track_uri)
                track_uris.append(track_uri)
            else:
                logger.warning("⚠️ Could not find track: %s", recommended_track)

        random.shuffle(track_uris)
        track_uris = track_uris[:limit]

        if track_uris:
            self.spotify.playlist_add_items(playlist["id"], track_uris)
            logger.info("[PlaylistGenerator] Added %d tracks to playlist %s", len(track_uris), playlist_name)
        else:
            logger.warning("[PlaylistGenerator] No tracks found to add")

if __name__ == "__main__":
    from echoseed.api.auth import SpotifyAuthService

    auth = SpotifyAuthService()
    auth.authenticate()
    sp_client = auth.get_spotify_client()

    generator = PlaylistGenerator(sp_client, "hype")
    mood_clusters = generator.get_clusters_for_mood()
    logger.info("[Main] Matching clusters for 'hype': %s", mood_clusters)
