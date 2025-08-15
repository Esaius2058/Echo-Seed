import json
import os
import pandas as pd
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai

client = genai.Client()

load_dotenv()

class MoodTagger:
    def __init__(self, client):
        self.client = client

    def get_clusters(self) -> dict:
        base_dir = Path(__file__).resolve().parents[2]
        csv_path = base_dir / "data" / "processed" / "clustered_tracks.csv"

        df = pd.read_csv(csv_path)
        clusters = {}
        for cluster, group in df.groupby("cluster"):
            clusters[int(cluster)] = group.to_dict(orient="records")

        return clusters

    def generate_prompt(self, tracks) -> str:
        prompt = "Assign a single mood to the following playlist based on audio features:\n\n"
        for i, track in enumerate(tracks[:8]):
            prompt += (f"Track {i + 1}: tempo={track['tempo']}, danceability={track['danceability']}, "
                       f"energy={track['energy']}, valence={track['valence']}\n")
        prompt += "\nReply with just one lowercase mood label (e.g., 'chill', 'hype', 'romantic', 'sad').\nMood:"
        return prompt

    def get_gpt_label(self, prompt, model="gemini-2.5-flash") -> str:
        response = client.models.generate_content(model=model, contents=prompt)
        first_candidate = response["candidates"][0]
        text_response = first_candidate["content"]["parts"][0]["text"]

        match = re.search(r"\bmood (is|:)\s*(\w+)", text_response.lower())
        label = match.group(2) if match else "unknown"
        return label

    def get_cached_label(self, cluster_id, cache) -> str:
        return cache.get(str(cluster_id), None)

    def cache_result(self, cluster_id, mood_label, cache, cache_file):
        cache[str(cluster_id)] = mood_label
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def fallback_label(self, tracks) -> str:
        # Average feature values across the cluster
        avg_tempo = sum(t['tempo'] for t in tracks) / len(tracks)
        avg_energy = sum(t['energy'] for t in tracks) / len(tracks)
        avg_valence = sum(t['valence'] for t in tracks) / len(tracks)
        avg_danceability = sum(t['danceability'] for t in tracks) / len(tracks)

        # Simple rule-based logic (you can tweak this)
        if avg_energy > 0.7 and avg_valence > 0.6:
            return "hype"
        elif avg_valence < 0.3 and avg_energy < 0.4:
            return "sad"
        elif avg_danceability > 0.6 and avg_energy < 0.6:
            return "chill"
        elif avg_valence > 0.5 and avg_energy < 0.5:
            return "romantic"
        else:
            return "moody"

    def main(self):
        cache_file = "mood_cache.json"
        output_file = "cluster_mood_map.json"

        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cache = json.load(f)
        else:
            cache = {}

        clusters = self.get_clusters()
        result = {}

        for cluster, tracks in clusters.items():
            label = self.get_cached_label(cluster, cache)
            if label:
                print(f"Using cached label for cluster {cluster}")
            else:
                prompt = self.generate_prompt(tracks)
                try:
                    label = self.get_gpt_label(prompt)
                    print(f"GPT label for cluster {cluster}: {label}")
                except:
                    print(f"Falling back for cluster {cluster}")
                    label = self.fallback_label(tracks)
                    print(f"Label {label}")
                self.cache_result(cluster, label, cache, cache_file)

            result[cluster] = label

        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

if __name__ == "__main__":
    tagger = MoodTagger(client)
    tagger.main()