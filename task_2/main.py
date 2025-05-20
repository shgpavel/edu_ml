# SPDX-License-Identifier: Apache-2.0

import torch

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import fetch_california_housing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def r2_score_manual(y_true, y_pred):
    ss_res = ((y_true - y_pred) ** 2).sum()
    ss_tot = ((y_true - y_true.mean()) ** 2).sum()
    return 1 - ss_res / ss_tot

def get_device():
    if torch.cuda.is_available():
        return torch.device('cuda')
    if getattr(torch.backends, 'xpu', None) and torch.xpu.is_available():
        return torch.device('cpu')
    if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available():
        return torch.device('mps')
    return torch.device('cpu')

def main():
    housing = fetch_california_housing(as_frame=True)
    df = pd.concat([housing.data, housing.target.rename('MedHouseVal')], axis=1)
    assert df.isnull().sum().sum() == 0

    X = housing.data.values.astype(np.float32)
    y = housing.target.values.reshape(-1, 1).astype(np.float32)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = np.hstack([np.ones((X_scaled.shape[0], 1), dtype=np.float32), X_scaled])

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    device = get_device()
    X_tr_t = torch.from_numpy(X_tr).to(device)
    y_tr_t = torch.from_numpy(y_tr).to(device)
    X_te_t = torch.from_numpy(X_te).to(device)
    y_te_t = torch.from_numpy(y_te).to(device)
    m, n = X_tr_t.shape

    XtX = X_tr_t.t() @ X_tr_t
    Xty = X_tr_t.t() @ y_tr_t
    theta_closed = torch.linalg.inv(XtX) @ Xty
    y_tr_pred_closed = X_tr_t @ theta_closed
    y_te_pred_closed = X_te_t @ theta_closed

    mse_tr_closed = torch.mean((y_tr_t - y_tr_pred_closed) ** 2).item()
    mse_te_closed = torch.mean((y_te_t - y_te_pred_closed) ** 2).item()
    r2_tr_closed = r2_score_manual(y_tr_t.cpu().numpy(), y_tr_pred_closed.cpu().numpy())
    r2_te_closed = r2_score_manual(y_te_t.cpu().numpy(), y_te_pred_closed.cpu().numpy())

    alpha = 0.01
    epochs = 700
    theta_gd = torch.randn(n, 1, device=device)
    mse_history = []
    for epoch in range(1, epochs + 1):
        preds = X_tr_t @ theta_gd
        error = preds - y_tr_t
        grad = (2 / m) * (X_tr_t.t() @ error)
        theta_gd -= alpha * grad
        mse_history.append(torch.mean(error ** 2).item())

    y_tr_pred_gd = X_tr_t @ theta_gd
    y_te_pred_gd = X_te_t @ theta_gd

    mse_tr_gd = torch.mean((y_tr_t - y_tr_pred_gd) ** 2).item()
    mse_te_gd = torch.mean((y_te_t - y_te_pred_gd) ** 2).item()
    r2_tr_gd = r2_score_manual(y_tr_t.cpu().numpy(), y_tr_pred_gd.cpu().numpy())
    r2_te_gd = r2_score_manual(y_te_t.cpu().numpy(), y_te_pred_gd.cpu().numpy())

    feature_names = ['Bias'] + housing.feature_names

    plt.figure(figsize=(8, 4))
    plt.plot(mse_history)
    plt.xlabel('Epoch')
    plt.ylabel('MSE')
    plt.title('Convergence of Gradient Descent')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(6, 6))
    plt.scatter(y_te, y_te_pred_gd.cpu(), alpha=0.3)
    plt.plot([y_te.min(), y_te.max()], [y_te.min(), y_te.max()], '--')
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title('Actual vs Predicted (Test GD)')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 5))
    pd.Series(theta_gd.cpu().numpy().ravel(), index=feature_names).plot.bar()
    plt.xticks(rotation=45)
    plt.title('Feature Coefficients (GD)')
    plt.grid(axis='y')
    plt.show()

    corr = housing.data.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt='0.2f', cmap='coolwarm')
    plt.title('Correlation Matrix')
    plt.show()

    print("\n=== Результаты: Метод наименьших квадратов (МНК) ===")
    print(f"Train MSE: {mse_tr_closed:.4f} | Train R2: {r2_tr_closed:.4f}")
    print(f"Test  MSE: {mse_te_closed:.4f} | Test  R2: {r2_te_closed:.4f}\n")

    print("=== Результаты: Градиентный спуск (GD) ===")
    print(f"Train MSE: {mse_tr_gd:.4f} | Train R2: {r2_tr_gd:.4f}")
    print(f"Test  MSE: {mse_te_gd:.4f} | Test  R2: {r2_te_gd:.4f}\n")

    print("=== Сравнение методов ===")
    print(f"Difference in Test R2 (Closed - GD): {r2_te_closed - r2_te_gd:+.4f}")
    print(f"Difference in Test MSE (GD - Closed): {mse_te_gd - mse_te_closed:+.4f}\n")

    abs_coefs = pd.Series(torch.abs(theta_gd).cpu().numpy().ravel(), index=feature_names)
    print("Топ признаки |coef| (GD):", abs_coefs.sort_values(ascending=False).head(3).to_dict())

    strong_corrs = [(i, j, corr.loc[i,j])
                    for i in corr.columns for j in corr.columns
                    if i < j and abs(corr.loc[i,j]) > 0.75]
    print("\nСильные корреляции (|r|>0.75):")
    for i, j, val in strong_corrs:
        print(f" - {i} & {j}: {val:.2f}")

if __name__ == "__main__":
    main()
