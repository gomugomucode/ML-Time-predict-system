from __future__ import annotations

import datetime
from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .ml_service import WaitTimePredictor


class PredictWaitTimeView(APIView):
    """
    POST /api/predict/
    Real-time waiting-time prediction endpoint powered by RandomForest ML model
    with sub-millisecond Average Service Time (AST) analytical fallback.

    Payload format:
    {
        "queue_length": 8,          # int (required, >= 0)
        "hour_of_day": 14,          # int (optional 0-23, defaults to current UTC/local hour)
        "day_of_week": 1,           # int (optional 0-6, defaults to current day of week)
        "is_weekend": 0,            # int (optional 0 or 1, automatically derived if omitted)
        "active_counters": 1        # int (optional >= 1, defaults to 1)
    }
    """

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data

        # 1. Validate queue_length
        if "queue_length" not in data:
            return Response(
                {"error": "Missing required field 'queue_length'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            queue_length = int(data["queue_length"])
            if queue_length < 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Field 'queue_length' must be a non-negative integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Extract or infer temporal parameters
        now = datetime.datetime.now()

        try:
            hour_of_day = int(data.get("hour_of_day", now.hour))
            if not 0 <= hour_of_day <= 23:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Field 'hour_of_day' must be an integer between 0 and 23."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            day_of_week = int(data.get("day_of_week", now.weekday()))
            if not 0 <= day_of_week <= 6:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Field 'day_of_week' must be an integer between 0 and 6 (0=Monday, 6=Sunday)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            is_weekend = int(data.get("is_weekend", 1 if day_of_week >= 5 else 0))
            if is_weekend not in (0, 1):
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Field 'is_weekend' must be 0 or 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            active_counters = int(data.get("active_counters", 1))
            if active_counters < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Field 'active_counters' must be a positive integer (>= 1)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Execute prediction via in-memory Singleton Predictor
        predictor = WaitTimePredictor.get_instance()
        result = predictor.predict_detailed(
            queue_length=queue_length,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            active_counters=active_counters,
        )

        return Response(
            {
                "status": "success",
                "predicted_wait_minutes": result["predicted_wait_time_minutes"],
                "engine": result["engine"],
                "prediction_status": result["status"],
                "active_counters": result["active_counters"],
                "features": result["features_used"],
                "inference_latency_ms": result["latency_ms"],
            },
            status=status.HTTP_200_OK,
        )
