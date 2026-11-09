"""
API HTTP Client Test Script
===========================
Sends a sample POST request to the local running Django prediction endpoint:
http://127.0.0.1:8000/api/predict/
"""

import sys
import requests

URL = "http://127.0.0.1:8000/api/predict/"

payload = {
    "queue_length": 10,
    "hour_of_day": 14,
    "day_of_week": 2,
    "is_weekend": 0,
    "active_counters": 1,
}

print(f"Connecting to: {URL}...")
print(f"Sending payload: {payload}\n")

try:
    response = requests.post(URL, json=payload, timeout=5)
    print("=" * 60)
    print("HTTP Status Code:", response.status_code)
    print("=" * 60)
    print("Response JSON:")
    import json
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("\n[!] Connection Error: Could not connect to Django server at http://127.0.0.1:8000/")
    print("    Please make sure your Django development server is running in another terminal:")
    print("    cd queue_backend")
    print("    python manage.py runserver\n")
    sys.exit(1)

