import os
import json
import pytest
from backend.analyzers.url_analyzer import UrlAnalyzer
from backend.analyzers.qr_analyzer import QrAnalyzer
from backend.analyzers.txn_analyzer import TransactionAnalyzer

def test_all_sample_data_accuracy_and_print_table():
    url_analyzer = UrlAnalyzer()
    qr_analyzer = QrAnalyzer(url_analyzer=url_analyzer)
    txn_analyzer = TransactionAnalyzer()

    # Load samples
    with open("sample_data/urls.json") as f:
        url_samples = json.load(f)
    with open("sample_data/qr_payloads.json") as f:
        qr_samples = json.load(f)
    with open("sample_data/transactions.json") as f:
        txn_samples = json.load(f)

    results = []

    # 1. URL Samples
    for sample in url_samples:
        res = url_analyzer.analyze(sample["url"])
        expected = sample["expected_risk_level"]
        actual = res["risk_level"]
        score = res["risk_score"]

        # Quality bar: safe items LOW, malicious items MEDIUM or HIGH
        if expected == "LOW":
            passed = (actual == "LOW")
        else:
            passed = (actual in ["MEDIUM", "HIGH"])

        results.append({
            "type": "URL",
            "identifier": sample["url"][:38] + ("..." if len(sample["url"]) > 38 else ""),
            "expected": expected,
            "actual": actual,
            "score": score,
            "passed": passed,
        })

    # 2. QR Samples
    for sample in qr_samples:
        res = qr_analyzer.analyze(sample["qr_payload"])
        expected = sample["expected_risk_level"]
        actual = res["risk_level"]
        score = res["risk_score"]

        if expected == "LOW":
            passed = (actual == "LOW")
        else:
            passed = (actual in ["MEDIUM", "HIGH"])

        results.append({
            "type": "QR",
            "identifier": sample["qr_payload"][:38] + ("..." if len(sample["qr_payload"]) > 38 else ""),
            "expected": expected,
            "actual": actual,
            "score": score,
            "passed": passed,
        })

    # 3. Transaction Samples
    for sample in txn_samples:
        req = sample["request"]
        res = txn_analyzer.analyze(
            user_id=req["user_id"],
            amount=req["amount"],
            receiver=req["receiver"],
            timestamp_str=req["timestamp"],
            channel=req.get("channel", "upi"),
            note=req.get("note", ""),
        )
        expected = sample["expected_risk_level"]
        actual = res["risk_level"]
        score = res["risk_score"]

        if expected == "LOW":
            passed = (actual == "LOW")
        else:
            passed = (actual in ["MEDIUM", "HIGH"])

        results.append({
            "type": "TXN",
            "identifier": f"{req['user_id']}: ₹{req['amount']} -> {req['receiver']}"[:38],
            "expected": expected,
            "actual": actual,
            "score": score,
            "passed": passed,
        })

    # Print formatted table
    header = f"{'Type':<6} | {'Target Identifier':<40} | {'Expected':<8} | {'Actual':<8} | {'Score':<5} | {'Result':<6}"
    sep = "-" * len(header)
    print("\n" + sep)
    print("PAYGUARD AI - SAMPLE DATA VALIDATION REPORT")
    print(sep)
    print(header)
    print(sep)

    all_passed = True
    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(f"{r['type']:<6} | {r['identifier']:<40} | {r['expected']:<8} | {r['actual']:<8} | {r['score']:<5} | {status_str:<6}")

    print(sep)
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"Summary: {passed_count}/{total} passed ({passed_count/total*100:.1f}%)\n")

    assert all_passed, "One or more sample items failed quality bar requirements!"
