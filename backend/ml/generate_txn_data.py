import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd

random.seed(42)

KNOWN_RECEIVERS = [
    "grocery@okaxis", "zomato@icici", "swiggy@okhdfcbank", "friend_rahul@ybl",
    "electric_bill@sbi", "amazon_pay@apl", "flipkart@axisbank", "deli_mart@okicici",
    "chai_point@paytm", "landlord_mehta@hdfcbank", "metro_recharge@sbi"
]

NORMAL_NOTES = [
    "chai", "groceries", "lunch", "dinner", "movie", "recharge",
    "rent", "split bill", "shopping", "cabs", ""
]

URGENT_NOTES = [
    "urgent refund", "kyc verification charge", "account blocked penalty",
    "lottery prize fee", "winner tax clearance", "immediate transfer required",
    "security deposit refund", "cashback claim fee"
]

USERS = {
    "u101": {"mean": 850.0, "std": 450.0, "usual_hours": [9, 22], "daily_limit": 100000.0},
    "u102": {"mean": 2400.0, "std": 1200.0, "usual_hours": [8, 23], "daily_limit": 100000.0},
    "u103": {"mean": 350.0, "std": 180.0, "usual_hours": [10, 21], "daily_limit": 50000.0},
    "u_default": {"mean": 1200.0, "std": 800.0, "usual_hours": [8, 22], "daily_limit": 100000.0},
}

def generate_user_baselines() -> Dict[str, Any]:
    """Generates baseline profiles for users, including known receivers and spending statistics."""
    baselines = {}
    for uid, profile in USERS.items():
        user_receivers = random.sample(KNOWN_RECEIVERS, k=random.randint(4, len(KNOWN_RECEIVERS) - 2))
        baselines[uid] = {
            "user_id": uid,
            "avg_amount": profile["mean"],
            "std_amount": profile["std"],
            "usual_hours": profile["usual_hours"],
            "daily_limit": profile["daily_limit"],
            "known_receivers": user_receivers,
        }
    return baselines

def generate_synthetic_transactions(n_records: int = 5000) -> pd.DataFrame:
    """Generate realistic transaction records (normal and anomalous)."""
    baselines = generate_user_baselines()
    records: List[Dict[str, Any]] = []

    start_date = datetime(2026, 1, 1, 0, 0, 0)

    for i in range(n_records):
        uid = random.choice(list(USERS.keys()))
        profile = baselines[uid]

        # 90% normal, 10% anomalous
        is_anomaly = random.random() < 0.10

        if not is_anomaly:
            # Normal transaction
            hour = random.randint(profile["usual_hours"][0], profile["usual_hours"][1])
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            day_offset = random.randint(0, 90)
            txn_time = start_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

            amount = max(10.0, round(random.gauss(profile["avg_amount"], profile["std_amount"]), 2))
            receiver = random.choice(profile["known_receivers"])
            note = random.choice(NORMAL_NOTES)
            label = 0
        else:
            # Anomalous transaction
            day_offset = random.randint(0, 90)
            hour = random.choice([1, 2, 3, 4]) # Odd night hour
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            txn_time = start_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)

            # High amount or near limit
            if random.random() < 0.7:
                amount = float(random.choice([49999, 50000, 85000, 95000, 99999]))
            else:
                amount = round(profile["avg_amount"] * random.uniform(5.0, 15.0), 2)

            receiver = random.choice(["unknown@ybl", "refund-desk@axl", "scam_wallet@okaxis", "unregistered@upi"])
            note = random.choice(URGENT_NOTES)
            label = 1

        records.append({
            "user_id": uid,
            "amount": amount,
            "receiver": receiver,
            "timestamp": txn_time.isoformat(),
            "channel": "upi",
            "note": note,
            "is_anomaly": label,
        })

    return pd.DataFrame(records)

def main():
    baselines = generate_user_baselines()
    with open("backend/ml/txn_baselines.json", "w") as f:
        json.dump(baselines, f, indent=2)
    print("User transaction baselines saved to backend/ml/txn_baselines.json")

    df = generate_synthetic_transactions(5000)
    df.to_csv("backend/ml/txn_dataset.csv", index=False)
    print(f"Synthetic transaction dataset saved ({len(df)} records)")

if __name__ == "__main__":
    main()
