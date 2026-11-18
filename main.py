"""
Root Entrypoint Wrapper -> Delegates to Django Backend ML Trainer
=================================================================
The canonical ML data ingestion, feature engineering, RandomForestRegressor
training, evaluation, and Joblib serialization pipeline now lives directly
inside the Django backend at:

    queue_backend/api/ml_trainer.py

You can train or retrain the model either via Django's management command:
    python queue_backend/manage.py train_model

Or by running this legacy wrapper script:
    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add `queue_backend` to Python path so `api.ml_trainer` resolves cleanly
BACKEND_DIR = Path(__file__).resolve().parent / "queue_backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.ml_trainer import (  # noqa: E402
    DEFAULT_MODEL_OUTPUT_PATH,
    extract_arrival_features,
    load_queue_datasets,
    train_and_evaluate_model,
    train_and_save_model,
)

PATH = "data"

__all__ = [
    "PATH",
    "DEFAULT_MODEL_OUTPUT_PATH",
    "load_queue_datasets",
    "extract_arrival_features",
    "train_and_evaluate_model",
    "train_and_save_model",
]


if __name__ == "__main__":
    train_and_save_model(data_path=PATH, output_path=DEFAULT_MODEL_OUTPUT_PATH, verbose=True)
