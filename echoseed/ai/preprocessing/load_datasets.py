from pathlib import Path
import pandas as pd

def load_spotify_dataset():
    base_dir = Path(__file__).resolve().parents[2]
    csv_path = base_dir / "data" / "raw" / "song_track.csv"

    print(f"Reading from: {csv_path}")
    df = pd.read_csv(csv_path)
    return df
