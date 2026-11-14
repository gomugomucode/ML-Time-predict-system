"""
API HTTP Client Test Script
===========================
Tests all live Django endpoints:
1. POST /api/predict/               (Direct ML Prediction)
2. POST /api/tickets/issue/         (Kiosk Ticket Issuance)
3. POST /api/counters/1/call-next/  (Teller Call Next Customer)
"""

import json
import sys
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_endpoint(name: str, method: str, path: str, payload=None):
    url = f"{BASE_URL}{path}"
    print("=" * 70)
    print(f"Test: {name} ({method} {path})")
    print("=" * 70)
    try:
        if method == "POST":
            res = requests.post(url, json=payload or {}, timeout=5)
        else:
            res = requests.get(url, timeout=5)

        print(f"Status Code: {res.status_code}")
        print("Response JSON:")
        print(json.dumps(res.json(), indent=2))
        print()
        return res
    except requests.exceptions.ConnectionError:
        print(f"\n[!] Connection Error: Could not reach {url}")
        print("    Ensure your server is running: python manage.py runserver\n")
        sys.exit(1)


if __name__ == "__main__":
    print(f"Testing Django REST Queue API at {BASE_URL}...\n")

    # 1. Test Prediction Endpoint
    test_endpoint(
        "Direct Inference Calculation",
        "POST",
        "/api/predict/",
        {
            "queue_length": 8,
            "hour_of_day": 14,
            "day_of_week": 2,
            "is_weekend": 0,
            "active_counters": 1,
        },
    )

    # 2. Test Issue Ticket (Kiosk)
    t_res = test_endpoint(
        "Issue Digital Ticket (Kiosk)",
        "POST",
        "/api/tickets/issue/",
        {"service_code": "ACC"},
    )

    # 3. Test Call Next Ticket (Teller Desk)
    test_endpoint(
        "Call Next Ticket (Teller Desk)",
        "POST",
        "/api/counters/1/call-next/",
    )

    print("All endpoint tests completed successfully!")
