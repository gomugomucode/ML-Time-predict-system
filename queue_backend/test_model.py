"""
Standalone Model Inference & Scenario Test Script
=================================================
Tests the serialized Random Forest wait-time prediction model across various
real-world queue scenarios (rush hour, off-peak, weekend, multi-counter).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import joblib
import pandas as pd

# 1. Resolve model artifact path (searches api/ dir, current dir, and repo root)
SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATE_PATHS = [
    SCRIPT_DIR / "api" / "wait_time_rf_model.joblib",
    SCRIPT_DIR / "wait_time_rf_model.joblib",
    SCRIPT_DIR.parent / "wait_time_rf_model.joblib",
]

model_path = None
for p in CANDIDATE_PATHS:
    if p.exists() and p.is_file():
        model_path = p
        break

if model_path is None:
    print(
        f"Error: Could not find 'wait_time_rf_model.joblib' in candidate paths: "
        f"{[str(p) for p in CANDIDATE_PATHS]}"
    )
    sys.exit(1)

print(f"Loading serialized model from: {model_path}...")
model = joblib.load(model_path)
print(f"Successfully loaded '{model_path.name}'!\n")

# 2. Define test scenarios (queue_length, hour_of_day, day_of_week, is_weekend, active_counters)
test_scenarios = [
    {
        "name": "Small Queue (Morning Off-Peak)",
        "queue_length": 2,
        "hour_of_day": 9,
        "day_of_week": 1,  # Tuesday
        "is_weekend": 0,
        "active_counters": 1,
    },
    {
        "name": "Heavy Rush (Afternoon Peak)",
        "queue_length": 15,
        "hour_of_day": 14,
        "day_of_week": 3,  # Thursday
        "is_weekend": 0,
        "active_counters": 1,
    },
    {
        "name": "Weekend Rush (Sunday Morning)",
        "queue_length": 5,
        "hour_of_day": 11,
        "day_of_week": 6,  # Sunday
        "is_weekend": 1,
        "active_counters": 1,
    },
    {
        "name": "Empty Queue (Immediate Service)",
        "queue_length": 0,
        "hour_of_day": 10,
        "day_of_week": 0,  # Monday
        "is_weekend": 0,
        "active_counters": 1,
    },
    {
        "name": "Heavy Rush with 2 Active Counters",
        "queue_length": 15,
        "hour_of_day": 14,
        "day_of_week": 3,  # Thursday
        "is_weekend": 0,
        "active_counters": 2,
    },
]

# 3. Features required by the trained model
FEATURE_COLUMNS = ["queue_length", "hour_of_day", "day_of_week", "is_weekend"]

# 4. Generate predictions and display results
print("=" * 86)
print(f"{'#':<3} {'Scenario':<34} {'Queue':<7} {'Time':<12} {'Counters':<10} {'Est. Wait Time'}")
print("=" * 86)

day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

for i, scenario in enumerate(test_scenarios, 1):
    input_data = pd.DataFrame([{col: scenario[col] for col in FEATURE_COLUMNS}])

    start_t = time.perf_counter()
    pred_wait = float(model.predict(input_data)[0])
    latency_ms = (time.perf_counter() - start_t) * 1000.0

    # Multi-counter capacity scaling
    counters = scenario.get("active_counters", 1)
    if counters > 1:
        pred_wait = pred_wait / counters

    day_str = day_names[scenario["day_of_week"]]
    time_str = f"{day_str} {scenario['hour_of_day']:02d}:00"

    print(
        f"{i:<3} {scenario['name']:<34} {scenario['queue_length']:<7} {time_str:<12} "
        f"{counters:<10} {max(0.0, pred_wait):.2f} min  ({latency_ms:.2f} ms)"
    )

print("=" * 86)
print("\nAll model scenario tests executed successfully!")
