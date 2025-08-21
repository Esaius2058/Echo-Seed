import json
from pathlib import Path
from spotipy import Spotify
from ..api.auth import SpotifyAuthService

base_dir = Path(__file__).resolve().parents[2]
clustered_tracks_file = base_dir / "echoseed" / "data" / "processed" / "clustered_tracks.csv"
mood_labels_file = base_dir / "cluster_mood_map.json"

class PlaylistCLI:
    def __init__(self, sp_client: Spotify):
        self.spotify = sp_client
        with open(clustered_tracks_file, "r") as f:
            self.clustered_tracks = f.read()

        with open(mood_labels_file, "r") as f:
            self.mood_labels = json.load(f)

        self.selected_mood_label = ""

    def display_menu(self):
        print("=== Echo Seed ===")
        print("...Cultivating Soundscapes...")
        print("Select a mood:\n")
        values = list(self.mood_labels.values())
        for i, mood in enumerate(values, start=1):
            print(f"{i}. {mood}")

        while True:
            try:
                choice = int(input("\nEnter the number of your choice: ").strip())
                if 1 <= choice <= len(self.mood_labels):
                    self.selected_mood_label = values[choice - 1]
                    return self.selected_mood_label
                else:
                    print(f"Please enter a number between 1 and {len(self.mood_labels)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    auth = SpotifyAuthService()
    spotify_client = auth.get_spotify_client()
    cli = PlaylistCLI(spotify_client)
    selected_mood = cli.display_menu()
    print(f"Selected {selected_mood}. This is the PlaylistCLI class and its working correctly!!")
