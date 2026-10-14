# 06. Django REST Framework & Scikit-Learn Integration Guide

This guide explains how to serialize a trained scikit-learn model, load it into process memory at Django startup using a thread-safe singleton pattern, validate payloads using Django REST Framework serializers, and serve predictions with dual-engine fallback in under **10 milliseconds**.

---

## 1. Key Performance Rules & Anti-Patterns

- ❌ **Anti-Pattern (Disk I/O per Request):** Calling `joblib.load()` inside a view function forces the server to read 10–100 MB from disk on every HTTP request, inflating latency to 200–800 ms and causing memory leaks under concurrent load.
- ✔️ **Correct Pattern (In-Memory Singleton):** The model artifact is loaded once into RAM during application startup (`AppConfig.ready()`). Subsequent API requests access the warm model directly in memory, reducing latency to **3–8 milliseconds**.

---

## 2. Step 1: Model Serialization & Pipeline Packaging

During offline training, package the preprocessing transformers and estimator into a unified scikit-learn `Pipeline`. This eliminates training-serving skew by ensuring raw inputs undergo identical transformations:

```python
# train_and_export.py
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Define features
numeric_features = ["current_queue_length", "active_servers", "rolling_ast_7d"]
categorical_features = ["service_code", "hour_of_day", "day_of_week"]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
    ]
)

# Build unified pipeline
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
            ),
        ),
    ]
)

# Fit pipeline on training data
# pipeline.fit(X_train, y_train)

# Save artifact
MODEL_DIR = Path("backend/app_queue/ml_models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(pipeline, MODEL_DIR / "waiting_time_rf_v1.joblib")
print("Model pipeline exported successfully.")
```

---

## 3. Step 2: Thread-Safe In-Memory Singleton Service

Create an ML service wrapper module (`ml_service.py`) using the Singleton pattern:

```python
# backend/app_queue/ml_service.py
import logging
from pathlib import Path
import threading
import joblib
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATH = (
    Path(__file__).resolve().parent / "ml_models" / "waiting_time_rf_v1.joblib"
)


class WaitTimePredictor:
  """Thread-safe Singleton providing in-memory model inference."""

  _instance = None
  _lock = threading.Lock()
  _model = None

  @classmethod
  def get_instance(cls):
    if cls._instance is None:
      with cls._lock:
        if cls._instance is None:
          cls._instance = cls()
          cls._instance.load_model()
    return cls._instance

  def load_model(self):
    """Loads or reloads the serialized model artifact into memory."""
    with self._lock:
      if MODEL_PATH.exists():
        try:
          self._model = joblib.load(MODEL_PATH)
          logger.info(f"Loaded ML model pipeline from {MODEL_PATH}")
        except Exception as e:
          logger.error(
              f"Failed to load ML model from {MODEL_PATH}: {e}", exc_info=True
          )
          self._model = None
      else:
        logger.warning(
            f"Model file not found at {MODEL_PATH}. Dual-engine fallback will"
            " be active."
        )
        self._model = None

  def is_ready(self) -> bool:
    return self._model is not None

  def predict(self, feature_dict: dict) -> float:
    """Evaluates features against in-memory model.

    Returns predicted wait time in seconds (strictly non-negative).
    """
    if self._model is None:
      raise RuntimeError("Primary ML model is not available.")

    # Convert to single-row DataFrame to preserve feature column names
    df = pd.DataFrame([feature_dict])
    prediction = self._model.predict(df)[0]

    # Non-negative clipping
    return max(0.0, float(prediction))
```

---

## 4. Step 3: Application Warm-Up via Django AppConfig

To ensure the model is loaded before the first HTTP request hits the server, warm up the singleton in the `ready()` lifecycle hook:

```python
# backend/app_queue/apps.py
from django.apps import AppConfig


class QueueConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "app_queue"

  def ready(self):
    # Avoid re-initialization during management commands like makemigrations
    import sys

    if any(
        cmd in sys.argv
        for cmd in [
            "makemigrations",
            "migrate",
            "collectstatic",
            "test",
        ]
    ):
      return

    from .ml_service import WaitTimePredictor

    # Preload model into process memory
    predictor = WaitTimePredictor.get_instance()
    if predictor.is_ready():
      print(">>> ML Inference Engine preloaded into process RAM (Ready).")
    else:
      print(">>> ML Model artifact not found. Fallback AST engine active.")
```

---

## 5. Step 4: Input Validation via DRF Serializers

Define serializers to enforce rigorous type validation, value bounds, and defaults:

```python
# backend/app_queue/serializers.py
from rest_framework import serializers


class PredictWaitTimeSerializer(serializers.Serializer):
  service_code = serializers.CharField(max_length=20, required=True)
  current_queue_length = serializers.IntegerField(
      min_value=0,
      required=True,
      help_text="Number of customers ahead in queue",
  )
  active_servers = serializers.IntegerField(
      min_value=1,
      default=1,
      help_text="Number of operational teller windows",
  )
  rolling_ast_7d = serializers.FloatField(
      min_value=10.0,
      default=180.0,
      help_text="Historical average service time in seconds",
  )
  hour_of_day = serializers.IntegerField(
      min_value=0, max_value=23, required=True
  )
  day_of_week = serializers.IntegerField(
      min_value=0, max_value=6, required=True
  )
  is_priority = serializers.BooleanField(default=False)
```

---

## 6. Step 5: API View with Dual-Engine Fallback

The API view implements deterministic fallback: if the primary ML model is unready or throws an inference exception, it transparently falls back to the **Average Service Time (AST)** formula:

```python
# backend/app_queue/views.py
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ml_service import WaitTimePredictor
from .serializers import PredictWaitTimeSerializer

logger = logging.getLogger(__name__)


class PredictWaitTimeView(APIView):
  """Evaluates wait time with sub-10ms response and automatic fallback."""

  def post(self, request):
    serializer = PredictWaitTimeSerializer(data=request.data)
    if not serializer.is_valid():
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    features = serializer.validated_data
    predictor = WaitTimePredictor.get_instance()

    predicted_wait_seconds = 0.0
    engine_used = "scikit_learn_rf"

    if predictor.is_ready():
      try:
        # System A: Primary In-Memory ML Inference (< 10 ms)
        predicted_wait_seconds = predictor.predict(features)
      except Exception as err:
        logger.warning(
            f"ML inference failure, falling back to AST formula: {err}"
        )
        engine_used = "ast_fallback_baseline"
    else:
      engine_used = "ast_fallback_baseline"

    # System B: Deterministic AST / Analytical Fallback
    if engine_used == "ast_fallback_baseline":
      queue_count = features["current_queue_length"]
      active_servers = features["active_servers"]
      avg_service_time = features["rolling_ast_7d"]

      # Analytical AST multi-server formula: (Q + 1) * AST / c
      predicted_wait_seconds = ((queue_count + 1) * avg_service_time) / max(
          1, active_servers
      )

    return Response(
        {
            "predicted_wait_time_seconds": round(predicted_wait_seconds, 1),
            "predicted_wait_time_minutes": round(
                predicted_wait_seconds / 60.0, 1
            ),
            "current_queue_length": features["current_queue_length"],
            "active_servers": features["active_servers"],
            "engine": engine_used,
        },
        status=status.HTTP_200_OK,
    )
```

---

## 7. Step 6: Integration into Ticket Creation Endpoint

When a ticket is created at a kiosk, inference is computed inline and stored with the transaction:

```python
# backend/app_queue/views.py (snippet)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from rest_framework import status, views
from rest_framework.response import Response
from .models import Counter, PredictionLog, RollingServiceMetric, Service, Ticket, Transaction


class TicketCreateView(views.APIView):

  def post(self, request):
    service_id = request.data.get("service_id")
    customer_id = request.data.get("customer_id")
    branch_id = request.data.get("branch_id")

    service = Service.objects.get(pk=service_id)

    # 1. Capture real-time queue snapshot
    waiting_count = Transaction.objects.filter(
        service=service, transaction_status="waiting"
    ).count()

    active_counters = (
        Counter.objects.filter(
            services=service, current_status__in=["open", "serving"]
        )
        .distinct()
        .count()
        or 1
    )

    # 2. Fetch cached rolling AST
    metric = RollingServiceMetric.objects.filter(service=service).first()
    ast_seconds = (
        metric.ast_estimated_time_seconds
        if metric
        else service.avg_service_time_seconds
    )

    # 3. Formulate feature vector
    now = timezone.now()
    feature_dict = {
        "service_code": service.service_code,
        "current_queue_length": waiting_count,
        "active_servers": active_counters,
        "rolling_ast_7d": float(ast_seconds),
        "hour_of_day": now.hour,
        "day_of_week": now.weekday(),
    }

    # 4. Predict wait time (< 10 ms)
    predictor = WaitTimePredictor.get_instance()
    try:
      predicted_seconds = predictor.predict(feature_dict)
      engine = "scikit_learn_rf"
    except Exception:
      predicted_seconds = ((waiting_count + 1) * float(ast_seconds)) / float(
          active_counters
      )
      engine = "ast_fallback"

    # 5. Persist Ticket & Transaction
    ticket = Ticket.objects.create(
        branch_id=branch_id,
        customer_id=customer_id,
        ticket_number=f"{service.service_code}-{waiting_count + 1:03d}",
        people_in_front_at_arrival=waiting_count,
    )
    transaction = Transaction.objects.create(
        ticket=ticket,
        service=service,
        waiting_start_time=now,
        transaction_status="waiting",
    )

    # 6. Log prediction for auditing
    PredictionLog.objects.create(
        ticket=ticket,
        predicted_wait_time_seconds=predicted_seconds,
        baseline_ast_prediction_seconds=(
            (waiting_count + 1) * float(ast_seconds)
        )
        / float(active_counters),
        engine_used=engine,
    )

    # 7. Broadcast via WebSockets
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"queue_{service.department_id}",
        {
            "type": "queue.updated",
            "event": "ticket_created",
            "ticket_number": ticket.ticket_number,
            "waiting_count": waiting_count + 1,
            "predicted_wait_min": round(predicted_seconds / 60.0, 1),
        },
    )

    return Response(
        {
            "ticket_id": ticket.ticket_id,
            "ticket_number": ticket.ticket_number,
            "queue_position": waiting_count + 1,
            "estimated_wait_minutes": round(predicted_seconds / 60.0, 1),
            "engine": engine,
        },
        status=status.HTTP_201_CREATED,
    )
```

---

## 8. Production Server Considerations

1. **WSGI Worker Pre-forking (Gunicorn / uWSGI):**
   - With multiple workers (`gunicorn config.wsgi -w 4`), models loaded during application startup leverage Linux Copy-on-Write (CoW) memory sharing, minimizing total RAM overhead.
2. **Thread Safety:**
   - Scikit-learn estimators are thread-safe for `.predict()` calls provided internal state attributes are not mutated during runtime.
3. **Zero-Downtime Hot-Reloading:**
   - To update the model without dropping connections, a Celery worker downloads the new `.joblib` artifact, verifies it against validation tests, replaces the file atomically, and invokes `WaitTimePredictor.get_instance().load_model()`.
