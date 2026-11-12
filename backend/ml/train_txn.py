import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

from backend.ml.generate_txn_data import main as generate_txn_main

TXN_FEATURE_NAMES = [
    "amount_zscore",
    "is_odd_hour",
    "is_new_receiver",
    "velocity_last_hour",
    "is_round_number",
    "has_urgency_keyword",
    "amount_ratio_daily_limit",
]

URGENT_WORDS = ["urgent", "refund", "kyc", "winner", "prize", "blocked", "lottery", "penalty", "claim"]

def extract_transaction_features(
    amount: float,
    timestamp_str: str,
    receiver: str,
    note: str,
    user_baseline: dict,
    velocity_count: int = 1,
) -> dict:
    """Extract behavior features for a single transaction given user baseline."""
    avg = user_baseline.get("avg_amount", 1000.0)
    std = max(user_baseline.get("std_amount", 500.0), 1.0)
    limit = user_baseline.get("daily_limit", 100000.0)
    known_receivers = set(user_baseline.get("known_receivers", []))

    # Parse hour
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        hour = dt.hour
    except Exception:
        hour = 12

    z_score = max(0.0, (amount - avg) / std)
    is_odd_hour = 1.0 if 1 <= hour <= 5 else 0.0
    is_new = 1.0 if receiver.lower() not in [r.lower() for r in known_receivers] else 0.0
    velocity = float(velocity_count)
    is_round = 1.0 if (amount >= 500 and amount % 500 == 0) else 0.0

    note_lower = (note or "").lower()
    has_urgency = 1.0 if any(w in note_lower for w in URGENT_WORDS) else 0.0
    ratio_limit = min(2.0, amount / limit)

    return {
        "amount_zscore": float(z_score),
        "is_odd_hour": float(is_odd_hour),
        "is_new_receiver": float(is_new),
        "velocity_last_hour": float(velocity),
        "is_round_number": float(is_round),
        "has_urgency_keyword": float(has_urgency),
        "amount_ratio_daily_limit": float(ratio_limit),
    }

def train_txn_model():
    """Trains IsolationForest on synthetic transaction dataset."""
    os.makedirs("backend/ml", exist_ok=True)
    baseline_path = "backend/ml/txn_baselines.json"
    dataset_path = "backend/ml/txn_dataset.csv"

    if not os.path.exists(baseline_path) or not os.path.exists(dataset_path):
        generate_txn_main()

    with open(baseline_path, "r") as f:
        baselines = json.load(f)

    df = pd.read_csv(dataset_path)

    # Feature extraction for each transaction
    rows = []
    for _, row in df.iterrows():
        uid = row["user_id"]
        profile = baselines.get(uid, baselines.get("u_default", {
            "avg_amount": 1000.0, "std_amount": 500.0, "daily_limit": 100000.0, "known_receivers": []
        }))
        feats = extract_transaction_features(
            amount=float(row["amount"]),
            timestamp_str=str(row["timestamp"]),
            receiver=str(row["receiver"]),
            note=str(row.get("note", "")),
            user_baseline=profile,
            velocity_count=random_velocity if (random_velocity := 1) else 1,
        )
        rows.append([feats[name] for name in TXN_FEATURE_NAMES])

    X = np.array(rows)

    print(f"Training IsolationForest on {len(X)} transaction feature vectors...")
    # 10% expected anomaly contamination
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.10,
        random_state=42,
    )
    iso_forest.fit(X)

    artifact = {
        "model": iso_forest,
        "feature_names": TXN_FEATURE_NAMES,
    }

    joblib.dump(artifact, "backend/ml/txn_model.pkl")
    print("IsolationForest saved to backend/ml/txn_model.pkl")

if __name__ == "__main__":
    train_txn_model()
