import time
import requests

BASE_URL = "http://127.0.0.1:8000/api"

print("--- 1. Issuing 3 Tickets ---")
for i in range(1, 4):
    r = requests.post(f"{BASE_URL}/tickets/issue/", json={"service_code": "ACC"})
    print(f"Ticket #{i}:", r.json())
    time.sleep(1)

print("\n--- 2. Waiting 3 seconds so wait time is non-zero ---")
time.sleep(3)

print("--- 3. Calling the First Ticket to Counter 1 ---")
call_r = requests.post(f"{BASE_URL}/tickets/call/1/")
print("Called Ticket:", call_r.json())
