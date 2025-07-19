from echoseed.ai.preprocessing.load_datasets import load_spotify_dataset
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def normalize_audio_features():
    audio_features = load_spotify_dataset()

    features = ['tempo', 'danceability', 'energy', 'valence']
    audio_features = audio_features.dropna(subset=features)
    audio_features = audio_features[(audio_features[features] != 0).all(axis=1)]

    data = audio_features[features].copy()
    min_max_scaler = MinMaxScaler(feature_range=(1, 10))
    data = min_max_scaler.fit_transform(data)

    normalized_df = pd.DataFrame(data, columns=features)
    return normalized_df

if __name__ == "__main__":
    df = normalize_audio_features()
    df.to_csv("echoseed/data/processed/normalized_tracks.csv", index=False)
    print(df)
