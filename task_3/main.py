# SPDX-License-Identifier: Apache-2.0

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def load_data(test_size=0.2, random_state=42):
    data = load_breast_cancer()
    X, y = data.data, np.where(data.target == 0, -1, 1)
    return train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )


def train_builtin_svc(X_train, y_train, X_test, C):
    svc = SVC(kernel="linear", C=C)
    svc.fit(X_train, y_train)
    return svc.predict(X_test)


def train_custom_svm(X_train, y_train, X_test, C, lr, n_iters):
    n_samples, n_features = X_train.shape
    w = np.zeros(n_features)
    b = 0.0
    for _ in range(n_iters):
        indices = np.random.permutation(n_samples)
        for i in indices:
            xi, yi = X_train[i], y_train[i]
            cond = yi * (np.dot(w, xi) + b)
            if cond >= 1:
                grad_w = w
                grad_b = 0
            else:
                grad_w = w - C * yi * xi
                grad_b = -C * yi
            w -= lr * grad_w
            b -= lr * grad_b
    return np.sign(np.dot(X_test, w) + b)


def evaluate(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, pos_label=1),
        "recall": recall_score(y_true, y_pred, pos_label=1),
        "f1_score": f1_score(y_true, y_pred, pos_label=1),
    }


def visualize_pca(X_train, y_train, X_test, y_test, C, lr, n_iters):
    pca = PCA(n_components=2, random_state=42)
    X_train_2d = pca.fit_transform(X_train)
    X_test_2d = pca.transform(X_test)
    svc2d = SVC(kernel="linear", C=C).fit(X_train_2d, y_train)
    svm2d_pred = train_custom_svm(X_train_2d, y_train, X_test_2d, C, lr, n_iters)
    x_min, x_max = X_test_2d[:, 0].min() - 1, X_test_2d[:, 0].max() + 1
    y_min, y_max = X_test_2d[:, 1].min() - 1, X_test_2d[:, 1].max() + 1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200), np.linspace(y_min, y_max, 200))
    grid = np.c_[xx.ravel(), yy.ravel()]
    Z_svc = svc2d.predict(grid).reshape(xx.shape)
    Z_svm = train_custom_svm(X_train_2d, y_train, grid, C, lr, n_iters).reshape(
        xx.shape
    )
    plt.contourf(xx, yy, Z_svc, alpha=0.3)
    plt.scatter(X_test_2d[:, 0], X_test_2d[:, 1], c=y_test, edgecolors="k")
    plt.title(f"Built-in SVC (C={C}, PCA 2D)")
    plt.show()
    plt.contourf(xx, yy, Z_svm, alpha=0.3)
    plt.scatter(X_test_2d[:, 0], X_test_2d[:, 1], c=y_test, edgecolors="k")
    plt.title(f"Custom SVM (C={C}, PCA 2D)")
    plt.show()


def main():
    X_train, X_test, y_train, y_test = load_data()
    missing_train = np.isnan(X_train).sum()
    missing_test = np.isnan(X_test).sum()
    if missing_train > 0 or missing_test > 0:
        print(f"Found missing values: train={missing_train}, test={missing_test}")
        return
    scaler = StandardScaler().fit(X_train)
    X_train = scaler.transform(X_train)
    X_test = scaler.transform(X_test)
    lr, n_iters = 1e-3, 1000
    Cs = [0.01, 1.0, 100.0]
    svc_results = []
    svm_results = []
    for C in Cs:
        y_pred_svc = train_builtin_svc(X_train, y_train, X_test, C)
        y_pred_svm = train_custom_svm(X_train, y_train, X_test, C, lr, n_iters)
        svc_metrics = evaluate(y_test, y_pred_svc)
        svm_metrics = evaluate(y_test, y_pred_svm)
        svc_metrics["model"] = f"SVC C={C}"
        svm_metrics["model"] = f"Custom C={C}"
        svc_results.append(svc_metrics)
        svm_results.append(svm_metrics)
    df_svc = pd.DataFrame(svc_results).set_index("model")
    df_svm = pd.DataFrame(svm_results).set_index("model")
    print("\nBuilt-in SVC metrics for different C values:")
    print(df_svc.to_string(float_format=lambda x: f"{x:.4f}"))
    print("\nCustom SVM metrics for different C values:")
    print(df_svm.to_string(float_format=lambda x: f"{x:.4f}"))
    for C in Cs:
        visualize_pca(X_train, y_train, X_test, y_test, C, lr, n_iters)


if __name__ == "__main__":
    main()
