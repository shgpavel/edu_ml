# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from collections import Counter

from sklearn.datasets import load_digits
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans


def init_centroids(X, k, rng):
    idx = rng.choice(X.shape[0], k, replace=False)
    return X[idx].copy()


def assign_clusters(X, centroids):
    d = np.linalg.norm(X[:, None] - centroids[None], axis=2)
    return d.argmin(axis=1)


def update_centroids(X, labels, k, rng):
    c = np.empty((k, X.shape[1]))
    for i in range(k):
        m = X[labels == i]
        c[i] = m.mean(axis=0) if m.size else X[rng.randint(0, X.shape[0] - 1)]
    return c


def compute_sse(X, labels, centroids):
    diff = X - centroids[labels]
    return (diff**2).sum()


def kmeans_custom(X, k=10, n_init=10, max_iter=300, tol=1e-4, random_state=None):
    master = np.random.RandomState(random_state)
    best_sse = np.inf
    best_labels = None
    best_centroids = None
    best_iter = None
    for _ in range(n_init):
        rng = np.random.RandomState(master.randint(0, 2**32 - 1))
        centroids = init_centroids(X, k, rng)
        for it in range(max_iter):
            labels = assign_clusters(X, centroids)
            new_centroids = update_centroids(X, labels, k, rng)
            if np.linalg.norm(new_centroids - centroids) < tol:
                break
            centroids = new_centroids
        sse = compute_sse(X, labels, centroids)
        if sse < best_sse:
            best_sse, best_labels, best_centroids, best_iter = (
                sse,
                labels,
                centroids,
                it + 1,
            )
    return best_labels, best_centroids, best_sse, best_iter


def purity(pred, true):
    k = pred.max() + 1
    correct = 0
    for i in range(k):
        idx = pred == i
        if idx.sum():
            correct += Counter(true[idx]).most_common(1)[0][1]
    return correct / len(true)


def main():
    digits = load_digits()
    X = digits.data
    y = digits.target
    X_scaled = StandardScaler().fit_transform(X)

    lab_c, cen_c, sse_c, it_c = kmeans_custom(
        X_scaled, k=10, n_init=10, random_state=42
    )

    km = KMeans(n_clusters=10, random_state=42, n_init=10)
    lab_s = km.fit_predict(X_scaled)

    metrics = pd.DataFrame(
        {
            "SSE": [sse_c, km.inertia_],
            "Silhouette": [
                silhouette_score(X_scaled, lab_c),
                silhouette_score(X_scaled, lab_s),
            ],
            "Davies_Bouldin": [
                davies_bouldin_score(X_scaled, lab_c),
                davies_bouldin_score(X_scaled, lab_s),
            ],
            "Purity": [purity(lab_c, y), purity(lab_s, y)],
            "Iterations": [it_c, km.n_iter_],
        },
        index=["Custom", "Sklearn"],
    )

    print(metrics)

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    plt.figure(figsize=(7, 5))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=lab_c, s=15)
    plt.title("Custom K-Means")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")

    plt.figure(figsize=(7, 5))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=lab_s, s=15)
    plt.title("Sklearn KMeans")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")

    d_c = np.linalg.norm(X_scaled - cen_c[lab_c], axis=1)
    d_s = np.linalg.norm(X_scaled - km.cluster_centers_[lab_s], axis=1)

    plt.figure(figsize=(6, 4))
    plt.hist(d_c, bins=30)
    plt.title("Custom distances")

    plt.figure(figsize=(6, 4))
    plt.hist(d_s, bins=30)
    plt.title("Sklearn distances")

    plt.show()


if __name__ == "__main__":
    main()
