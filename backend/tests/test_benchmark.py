import time
import numpy as np
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_p95_latency_under_300ms():
    endpoints_and_payloads = [
        ("/api/analyze/url", {"url": "http://paytm-secure-login.xyz/verify?id=123"}),
        ("/api/analyze/qr", {"qr_payload": "upi://pay?pa=shop@okaxis&pn=Ram Store&am=5000&cu=INR"}),
        ("/api/analyze/transaction", {
            "user_id": "u101",
            "amount": 49999,
            "receiver": "unknown@ybl",
            "timestamp": "2026-11-12T02:14:00",
            "channel": "upi",
            "note": "urgent refund"
        }),
    ]

    # Warm up
    for endpoint, payload in endpoints_and_payloads:
        client.post(endpoint, json=payload)

    iterations = 35
    for endpoint, payload in endpoints_and_payloads:
        durations = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            res = client.post(endpoint, json=payload)
            t1 = time.perf_counter()
            assert res.status_code == 200
            durations.append((t1 - t0) * 1000.0) # ms

        p95 = float(np.percentile(durations, 95))
        avg = float(np.mean(durations))
        print(f"\nBenchmark {endpoint}: avg={avg:.2f}ms, p95={p95:.2f}ms (Target: <300ms)")
        assert p95 < 300.0, f"{endpoint} p95 latency {p95:.2f}ms exceeded 300ms threshold!"
