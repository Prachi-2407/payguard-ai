import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import joblib

# Set non-interactive backend and writable config directory for matplotlib
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

from backend.ml.features import extract_url_features, FEATURE_NAMES, features_dict_to_vector
from backend.ml.generate_data import main as generate_data_main

METRICS_PATH = "backend/ml/metrics.json"
MODEL_PATH = "backend/ml/url_model.pkl"
CONFUSION_MATRIX_PATH = "backend/ml/confusion_matrix.png"
DATASET_PATH = "backend/ml/dataset.csv"

def extract_dataset_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Extract features for every URL in the dataframe."""
    print(f"Extracting features for {len(df)} URLs...")
    feature_rows = []
    for url in df["url"]:
        feats = extract_url_features(url)
        feature_rows.append(features_dict_to_vector(feats))

    X = np.array(feature_rows)
    y = df["label"].values
    return X, y

def train_and_evaluate(
    dataset_csv: str = DATASET_PATH,
    n_samples_if_missing: int = 10000,
    force_regenerate: bool = False,
) -> dict:
    """
    Main training routine:
    1. Loads or generates dataset
    2. Extracts feature matrix
    3. Cross-validates RandomForest vs GradientBoosting
    4. Trains best model on train split, evaluates on test split
    5. Saves metrics.json, confusion_matrix.png, and url_model.pkl
    """
    os.makedirs("backend/ml", exist_ok=True)

    if force_regenerate or not os.path.exists(dataset_csv):
        df = generate_data_main(n_samples=n_samples_if_missing, output_path=dataset_csv)
    else:
        print(f"Loading existing dataset from {dataset_csv}...")
        df = pd.read_csv(dataset_csv)

    X, y = extract_dataset_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    rf_candidate = RandomForestClassifier(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    )
    gb_candidate = GradientBoostingClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
    )

    print("Running 5-fold cross-validation on RandomForestClassifier...")
    rf_cv_scores = cross_val_score(rf_candidate, X_train, y_train, cv=cv, scoring="f1", n_jobs=-1)
    rf_mean_f1 = float(np.mean(rf_cv_scores))
    print(f"RandomForest Mean CV F1: {rf_mean_f1:.4f}")

    print("Running 5-fold cross-validation on GradientBoostingClassifier...")
    gb_cv_scores = cross_val_score(gb_candidate, X_train, y_train, cv=cv, scoring="f1", n_jobs=-1)
    gb_mean_f1 = float(np.mean(gb_cv_scores))
    print(f"GradientBoosting Mean CV F1: {gb_mean_f1:.4f}")

    if rf_mean_f1 >= gb_mean_f1:
        chosen_name = "RandomForestClassifier"
        best_model = rf_candidate
    else:
        chosen_name = "GradientBoostingClassifier"
        best_model = gb_candidate

    print(f"Selected best model: {chosen_name}")
    best_model.fit(X_train, y_train)

    y_pred = best_model.predict(X_test)
    y_prob = best_model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred)

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        raw_importances = best_model.feature_importances_
        feature_importance_list = [
            {"feature": name, "importance": round(float(imp), 4)}
            for name, imp in sorted(
                zip(FEATURE_NAMES, raw_importances),
                key=lambda x: x[1],
                reverse=True,
            )
        ]
    else:
        feature_importance_list = []

    metrics_payload = {
        "best_model": chosen_name,
        "cross_validation": {
            "RandomForest_mean_f1": round(rf_mean_f1, 4),
            "GradientBoosting_mean_f1": round(gb_mean_f1, 4),
        },
        "test_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
        },
        "confusion_matrix": {
            "true_negatives": int(cm[0][0]),
            "false_positives": int(cm[0][1]),
            "false_negatives": int(cm[1][0]),
            "true_positives": int(cm[1][1]),
        },
        "top_features": feature_importance_list[:10],
    }

    # Save metrics JSON
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Metrics saved to {METRICS_PATH}")

    # Plot & save confusion matrix
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    classes = ["Legitimate", "Phishing"]
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=classes,
        yticklabels=classes,
        title=f"Confusion Matrix ({chosen_name})",
        ylabel="True Label",
        xlabel="Predicted Label",
    )
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black"
            )
    fig.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix saved to {CONFUSION_MATRIX_PATH}")

    # Save trained model artifact
    model_artifact = {
        "model": best_model,
        "model_name": chosen_name,
        "feature_names": FEATURE_NAMES,
        "feature_importances": feature_importance_list,
    }
    joblib.dump(model_artifact, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return metrics_payload

if __name__ == "__main__":
    train_and_evaluate()
