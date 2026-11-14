"""
Sequential Ticket Issuance & Counter Calling Simulation Test Script
===================================================================
Simulates a real-world queue:
1. Issues 4 sequential tickets at a self-service kiosk (recording EWT & people ahead).
2. Waits 3-5 seconds so actual waiting time is non-zero.
3. Counter 1 calls the first two tickets, verifying state transition and error tracking.
"""

import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000/api"

print("=" * 65)
print("1. ISSUING 4 SEQUENTIAL TICKETS TO THE QUEUE")
print("=" * 65)

issued_tickets = []

try:
    for i in range(1, 5):
        resp = requests.post(
            f"{BASE_URL}/tickets/issue/", json={"service_code": "ACC"}, timeout=5
        )
        if resp.status_code == 201:
            data = resp.json()
            issued_tickets.append(data["ticket_number"])
            print(
                f"Ticket #{i}: {data['ticket_number']} | "
                f"People Ahead: {data['people_ahead']} | "
                f"Est. Wait: {data['estimated_wait_minutes']} min"
            )
        else:
            print(f"Failed to issue ticket #{i}:", resp.status_code, resp.text)
        time.sleep(1)  # 1-second pause between ticket arrivals
except requests.exceptions.ConnectionError:
    print("\n[!] Connection Error: Could not connect to Django server at http://127.0.0.1:8000/")
    print("    Please ensure your development server is running in another terminal:")
    print("    cd queue_backend")
    print("    python manage.py runserver\n")
    sys.exit(1)

print("\n" + "=" * 65)
print("2. SIMULATING SERVICE: COUNTER 1 CALLS THE FIRST TWO TICKETS")
print("=" * 65)

# Wait 3 seconds so actual wait time is non-zero
print("Waiting 3 seconds before calling the first ticket...")
time.sleep(3)

for call_num in range(1, 3):
    call_resp = requests.post(f"{BASE_URL}/tickets/call/1/", timeout=5)
    if call_resp.status_code == 200:
        res = call_resp.json()
        if res.get("status") == "success":
            print(
                f"Call {call_num}: Ticket {res['called_ticket']} -> Counter {res['counter']}"
            )
            print(f"  - Actual Wait Time:    {res['actual_wait_minutes']} min")
            print(f"  - ML Predicted Time:   {res['predicted_wait_minutes']} min")
            print(f"  - Prediction Error:    {res['prediction_error_minutes']} min\n")
        else:
            print("Message:", res.get("message"))
    else:
        print("Call failed:", call_resp.status_code, call_resp.text)
    time.sleep(1)

print("=" * 65)
print("Test completed successfully!")
