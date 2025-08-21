import os
import random
from pathlib import Path
from dotenv import load_dotenv
from spotipy import Spotify
from openai import OpenAI, base_url

load_dotenv()

base_dir = Path(__file__).resolve().parents[2]
clustered_tracks_file = base_dir / "echo-seed" / "data" / "processed" / "clustered_tracks.csv"
mood_labels_file = base_dir / "cluster_mood_map.json"

class PlaylistGenerator:
    def __init__(self, spotify_client: Spotify, mood):
        self.spotify = spotify_client
        self.user = self.spotify.user(self.spotify.me())
        self.mood = mood
        self.ai_client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        with open(clustered_tracks_file, "r") as f:
            self.clustered_tracks = f.read()

        with open(mood_labels_file, "r") as f:
            self.mood_labels = f.read()

    def get_clusters_for_mood(self) -> list:
        matching_clusters = []
        for cluster_id, label in self.mood_labels:
            if label == self.mood:
                matching_clusters.append(cluster_id)

        return matching_clusters

    def get_playlist_name(self) -> str:
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

        # Extract raw text
        names_text = response.choices[0].message.content.strip()

        # Split lines into individual names
        names = [line.strip("-• ").strip() for line in names_text.splitlines() if line.strip()]

        # Pick one at random
        return random.choice(names) if names else "Untitled Mix"

    def get_artists_from_playlists(self, user_id):
        artists = set()
        playlists = self.spotify.user_playlists(user_id, limit=10)

        for playlist in playlists["items"]:
            playlist_id = playlist.id

            tracks = self.spotify.playlist_items(playlist_id)

            while tracks:
                for item in tracks["items"]:
                    track = item.get("track")
                    if track:
                        for artist in track["artists"]:
                            artists.add(artist["name"])

                if tracks['next']:
                    tracks = self.spotify.next(tracks)
                else:
                    tracks = None

            return list(artists)

    def get_recommended_tracks(self, user_id, limit: int = 25):
        artists = self.get_artists_from_playlists(user_id)
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

        return recommendations[:limit]

    def generate_playlist(self, user_id, limit: int = 25):
        playlist_name = self.get_playlist_name()
        playlist = self.spotify.user_playlist_create(
            self.user,
            playlist_name,
            False,
        )

        track_uris = []
        recommended_tracks = self.get_recommended_tracks(user_id)
        for recommended_track in recommended_tracks:
            parts = recommended_track.split(" - ")
            if len(parts) == 2:
                name, artist = parts
            else:
                name, artist = recommended_track, ""

            query = f"{name} {artist}".strip()
            results = self.spotify.search(q=query, type="track", limit=1)

            items = results.get("tracks", {}).get("items", [])
            if items:
                track_uris.append(items[0]["uri"])
            else:
                print(f"⚠️ Could not find track: {recommended_track}")

        random.shuffle(track_uris)
        track_uris = track_uris[:limit]

        if track_uris:
            self.spotify.playlist_add_items(playlist["id"], track_uris)