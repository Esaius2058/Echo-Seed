from echoseed.ai.preprocessing.normalize_features import normalize_audio_features
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from joblib import dump

def optimise_k_means(data, max_k):
    means = []
    inertias = []

    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(data)

        means.append(k)
        inertias.append(kmeans.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(means, inertias, 'o-')
    plt.xlabel('Numbers of Clusters (k)')
    plt.ylabel('Inertia')
    plt.title("Elbow Method for Optimal k")
    plt.grid(True)
    plt.savefig("inertias.png")
    print("Inertia plot saved as inertias.png")

def cluster_features():
    df = normalize_audio_features()

    model = KMeans(n_clusters=4, random_state=42)
    labels = model.fit_predict(df)

    df["cluster"] = labels

    df.to_csv("echoseed/data/processed/clustered_tracks.csv", index=False)
    dump(model, "echoseed/model/clustering/kmeans_model.joblib")

    return df, model

cluster_features()