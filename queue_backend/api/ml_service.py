"""
ML Queue Waiting-Time Prediction Service (Singleton Inference Engine)
====================================================================
This module provides a production-grade, thread-safe, in-memory inference
engine for predicting queue waiting times in real-time.

Architecture Overview:
----------------------
1. Dual-Engine Redundancy:
   - Primary System A (Empirical ML):
     Trained RandomForestRegressor (100 trees) serialized via Joblib.
     Features: ['queue_length', 'hour_of_day', 'day_of_week', 'is_weekend'].
   - Fallback System B (Analytical AST Baseline):
     Average Service Time formula based on empirical ground-truth service rate
     (S_bar = 2.38 minutes per customer):
     W_AST = (queue_length * 2.38) / active_counters
     Ensures 100% uptime with sub-millisecond response even if model file is
     missing or corrupted.

2. In-Memory Singleton Pattern:
   - The 33MB model is deserialized once at application startup (via Django
     AppConfig.ready()) and held resident in RAM.
   - Prevents disk I/O bottlenecks and achieves sub-10ms inference SLA.
   - Thread safety is enforced using threading.RLock (reentrant lock) to prevent
     concurrent race conditions and reentrant deadlocks.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Ground-truth empirical constants derived from queue dataset analysis
DEFAULT_AVERAGE_SERVICE_TIME_MINUTES: float = 2.38  # S_bar from verified dataset
DEFAULT_ACTIVE_COUNTERS: int = 1
MODEL_FEATURE_NAMES: list[str] = [
    "queue_length",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
]

# Candidate search paths for the serialized model artifact
BASE_DIR = Path(__file__).resolve().parent
CANDIDATE_MODEL_PATHS: list[Path] = [
    BASE_DIR / "wait_time_rf_model.joblib",
    BASE_DIR.parent / "wait_time_rf_model.joblib",
    BASE_DIR.parent.parent / "wait_time_rf_model.joblib",
]


class WaitTimePredictor:
    """
    Thread-safe Singleton class providing wait-time inference using either
    the trained Random Forest ML model or analytical fallback formula.
    """

    _instance: Optional[WaitTimePredictor] = None
    _lock: threading.RLock = threading.RLock()

    def __init__(self) -> None:
        """
        Private-style initializer. Use `WaitTimePredictor.get_instance()` instead.
        """
        self.model: Any = None
        self.model_path: Optional[Path] = None
        self._is_loaded: bool = False
        self.load_model()

    @classmethod
    def get_instance(cls) -> WaitTimePredictor:
        """
        Thread-safe singleton accessor with double-checked locking pattern.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load_model(self) -> bool:
        """
        Search candidate directories and load the serialized Joblib model into RAM.
        Returns True if successfully loaded, False otherwise.
        """
        with self._lock:
            for path in CANDIDATE_MODEL_PATHS:
                if path.exists() and path.is_file():
                    try:
                        logger.info("Loading wait-time model from: %s", path)
                        self.model = joblib.load(path)
                        self.model_path = path
                        self._is_loaded = True
                        logger.info("Successfully loaded model into memory from %s", path)
                        return True
                    except Exception as err:
                        logger.error("Failed to load model from %s: %s", path, err, exc_info=True)

            logger.warning(
                "Model file 'wait_time_rf_model.joblib' not found in candidate paths: %s. "
                "Predictor will operate in Analytical AST Fallback mode.",
                [str(p) for p in CANDIDATE_MODEL_PATHS],
            )
            self.model = None
            self.model_path = None
            self._is_loaded = False
            return False

    def is_ready(self) -> bool:
        """Return True if the ML model is resident in RAM and ready for inference."""
        return self._is_loaded and self.model is not None

    def calculate_ast_fallback(
        self,
        queue_length: int,
        active_counters: int = DEFAULT_ACTIVE_COUNTERS,
        avg_service_time: float = DEFAULT_AVERAGE_SERVICE_TIME_MINUTES,
    ) -> float:
        """
        Analytical Fallback System B:
        Calculates expected wait time using Average Service Time (AST) formula:
            W_AST = (L_q * S_bar) / c
        """
        c = max(1, int(active_counters))
        l_q = max(0, int(queue_length))
        s_bar = max(0.1, float(avg_service_time))
        estimated_minutes = (l_q * s_bar) / c
        return round(float(estimated_minutes), 2)

    def predict_detailed(
        self,
        queue_length: int,
        hour_of_day: int,
        day_of_week: int,
        is_weekend: int,
        active_counters: int = DEFAULT_ACTIVE_COUNTERS,
        avg_service_time: float = DEFAULT_AVERAGE_SERVICE_TIME_MINUTES,
    ) -> Dict[str, Any]:
        """
        Execute prediction with end-to-end timing, telemetry, and automatic fallback.

        Returns:
            dict containing:
              - 'predicted_wait_time_minutes': float
              - 'engine': 'RandomForestRegressor' or 'AverageServiceTimeFallback'
              - 'status': 'success' or 'fallback'
              - 'features_used': dict
              - 'latency_ms': float
              - 'model_path': str or None
        """
        start_time = time.perf_counter()

        # Sanitize and validate inputs
        sanitized_queue_length = max(0, int(queue_length))
        sanitized_hour = max(0, min(23, int(hour_of_day)))
        sanitized_day = max(0, min(6, int(day_of_week)))
        sanitized_is_weekend = 1 if is_weekend or sanitized_day >= 5 else 0
        sanitized_counters = max(1, int(active_counters))

        features_dict = {
            "queue_length": sanitized_queue_length,
            "hour_of_day": sanitized_hour,
            "day_of_week": sanitized_day,
            "is_weekend": sanitized_is_weekend,
        }

        # Attempt ML inference (System A)
        if self.is_ready():
            try:
                # Construct 1-row DataFrame with identical schema used during model training
                input_df = pd.DataFrame([features_dict], columns=MODEL_FEATURE_NAMES)
                raw_pred = self.model.predict(input_df)[0]
                pred_minutes = round(max(0.0, float(raw_pred)), 2)

                # Adjust for multi-counter service capacity if more than 1 counter is active
                if sanitized_counters > 1:
                    pred_minutes = round(pred_minutes / sanitized_counters, 2)

                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
                return {
                    "predicted_wait_time_minutes": pred_minutes,
                    "engine": "RandomForestRegressor",
                    "status": "success",
                    "features_used": features_dict,
                    "active_counters": sanitized_counters,
                    "latency_ms": latency_ms,
                    "model_path": str(self.model_path) if self.model_path else None,
                }
            except Exception as exc:
                logger.error(
                    "ML inference failure, falling back to AST formula: %s",
                    exc,
                    exc_info=True,
                )

        # Fallback to Analytical AST Formula (System B)
        fallback_minutes = self.calculate_ast_fallback(
            queue_length=sanitized_queue_length,
            active_counters=sanitized_counters,
            avg_service_time=avg_service_time,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return {
            "predicted_wait_time_minutes": fallback_minutes,
            "engine": "AverageServiceTimeFallback",
            "status": "fallback",
            "features_used": features_dict,
            "active_counters": sanitized_counters,
            "latency_ms": latency_ms,
            "model_path": None,
        }


# Convenience functional interface
def predict_waiting_time(
    queue_length: int,
    hour_of_day: int,
    day_of_week: int,
    is_weekend: int,
    active_counters: int = DEFAULT_ACTIVE_COUNTERS,
) -> float:
    """
    High-level functional interface for predicting wait time in minutes.
    Delegates to the in-memory singleton predictor.
    """
    predictor = WaitTimePredictor.get_instance()
    result = predictor.predict_detailed(
        queue_length=queue_length,
        hour_of_day=hour_of_day,
        day_of_week=day_of_week,
        is_weekend=is_weekend,
        active_counters=active_counters,
    )
    return result["predicted_wait_time_minutes"]
