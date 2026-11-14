from __future__ import annotations

import datetime
from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.ml_service import WaitTimePredictor, predict_waiting_time
from api.models import Counter, PredictionLog, Service, Ticket


class ApiRootView(APIView):
    """
    GET / and GET /api/
    Root API directory providing links to active services, endpoints, and docs.
    """

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        predictor = WaitTimePredictor.get_instance()
        return Response(
            {
                "service": "ML Queue Waiting-Time Prediction & Management System",
                "version": "1.0.0",
                "status": "online",
                "ml_engine_ready": predictor.is_ready(),
                "endpoints": {
                    "issue_ticket": request.build_absolute_uri("/api/tickets/issue/"),
                    "call_next_ticket": request.build_absolute_uri(
                        "/api/counters/1/call-next/"
                    ),
                    "predict_wait_time": request.build_absolute_uri("/api/predict/"),
                    "admin_dashboard": request.build_absolute_uri("/admin/"),
                },
                "quick_test_instructions": {
                    "issue_ticket": {
                        "method": "POST",
                        "url": request.build_absolute_uri("/api/tickets/issue/"),
                        "sample_body": {"service_code": "ACC"},
                    },
                    "call_next": {
                        "method": "POST",
                        "url": request.build_absolute_uri("/api/counters/1/call-next/"),
                    },
                    "predict_wait_time": {
                        "method": "POST",
                        "url": request.build_absolute_uri("/api/predict/"),
                        "sample_body": {
                            "queue_length": 8,
                            "hour_of_day": 14,
                            "active_counters": 2,
                        },
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


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

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Health and schema discovery endpoint for GET /api/predict/
        Returns current engine readiness, model artifact status, and payload schema.
        """
        predictor = WaitTimePredictor.get_instance()
        is_ready = predictor.is_ready()
        return Response(
            {
                "endpoint": "POST /api/predict/",
                "service": "Queue Wait Time Prediction API",
                "status": "ready" if is_ready else "fallback_mode",
                "active_engine": (
                    "RandomForestRegressor"
                    if is_ready
                    else "AverageServiceTimeFallback"
                ),
                "model_loaded": is_ready,
                "model_path": (
                    str(predictor.model_path) if predictor.model_path else None
                ),
                "required_parameters": {
                    "queue_length": "Non-negative integer (e.g. 8)"
                },
                "optional_parameters": {
                    "hour_of_day": "Integer 0-23 (defaults to current system hour)",
                    "day_of_week": "Integer 0-6 (0=Monday, 6=Sunday; defaults to today)",
                    "is_weekend": "0 or 1 (automatically derived if omitted)",
                    "active_counters": "Integer >= 1 (defaults to 1)",
                },
                "sample_request_payload": {
                    "queue_length": 8,
                    "hour_of_day": 14,
                    "day_of_week": 1,
                    "is_weekend": 0,
                    "active_counters": 2,
                },
            },
            status=status.HTTP_200_OK,
        )

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
                {
                    "error": "Field 'day_of_week' must be an integer between 0 and 6 (0=Monday, 6=Sunday)."
                },
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


class IssueTicketView(APIView):
    """
    POST /api/tickets/issue/
    Issues a new ticket token at the kiosk, counts the current queue ahead,
    predicts estimated wait time using the in-memory ML model, saves the ticket
    and creates an immutable prediction log for audit.

    Request Payload:
    {
        "service_code": "ACC"   # e.g., "ACC", "ADM", "EXM" (defaults to "ACC")
    }
    """

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        service_code = request.data.get("service_code", "ACC").upper().strip()

        # 1. Fetch or create service category
        service, _ = Service.objects.get_or_create(
            code=service_code, defaults={"name": f"{service_code} Service"}
        )

        # 2. Count active waiting tickets for this service
        current_waiting_count = Ticket.objects.filter(
            service=service, status="waiting"
        ).count()

        # 3. Extract instantaneous arrival features
        now = datetime.datetime.now()
        hour_of_day = now.hour
        day_of_week = now.weekday()
        is_weekend = 1 if day_of_week >= 5 else 0

        # Determine currently open counters (default to 1 if none configured)
        open_counters_count = Counter.objects.filter(is_open=True).count()
        active_counters = max(1, open_counters_count)

        # 4. Predict wait time via in-memory Singleton Predictor
        predictor = WaitTimePredictor.get_instance()
        pred_res = predictor.predict_detailed(
            queue_length=current_waiting_count,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            active_counters=active_counters,
        )
        predicted_wait = pred_res["predicted_wait_time_minutes"]
        engine_used = pred_res["engine"]
        latency_ms = pred_res["latency_ms"]

        # 5. Generate Ticket Token Number (e.g. ACC-001, ACC-002)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_ticket_count = (
            Ticket.objects.filter(service=service, created_at__gte=today_start).count()
            + 1
        )
        ticket_number = f"{service.code}-{daily_ticket_count:03d}"

        # 6. Save Ticket record to Database
        ticket = Ticket.objects.create(
            ticket_number=ticket_number,
            service=service,
            queue_length_at_arrival=current_waiting_count,
            predicted_wait_minutes=round(predicted_wait, 1),
            prediction_engine=engine_used,
            status="waiting",
        )

        # 7. Create immutable PredictionLog entry for model drift & SLA tracking
        PredictionLog.objects.create(
            ticket=ticket,
            predicted_wait_minutes=ticket.predicted_wait_minutes,
            engine_used=engine_used,
            inference_latency_ms=latency_ms,
            features_snapshot={
                "queue_length": current_waiting_count,
                "hour_of_day": hour_of_day,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "active_counters": active_counters,
            },
        )

        return Response(
            {
                "status": "success",
                "ticket_number": ticket.ticket_number,
                "service": service.name,
                "people_ahead": current_waiting_count,
                "estimated_wait_minutes": ticket.predicted_wait_minutes,
                "engine": engine_used,
                "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
            status=status.HTTP_201_CREATED,
        )


class CallNextTicketView(APIView):
    """
    POST /api/counters/<counter_id>/call-next/
    Teller desk action: Calls the oldest waiting customer to the specified counter,
    marks ticket as 'in_service', and computes ground-truth actual wait time W_q = t_S - t_A.
    """

    def post(
        self, request: Request, counter_id: int, *args: Any, **kwargs: Any
    ) -> Response:
        # 1. Fetch or create the counter
        counter, _ = Counter.objects.get_or_create(
            counter_number=int(counter_id),
            defaults={"name": f"Counter {counter_id}", "is_open": True},
        )

        # 2. Get the oldest waiting ticket in FIFO order
        next_ticket = (
            Ticket.objects.filter(status="waiting").order_by("created_at").first()
        )
        if not next_ticket:
            return Response(
                {
                    "status": "empty",
                    "message": "No tickets currently waiting in line.",
                    "counter": counter.counter_number,
                },
                status=status.HTTP_200_OK,
            )

        # 3. Mark ticket as called (updates status, called_at, actual_wait_minutes, and PredictionLog)
        next_ticket.mark_as_called(counter)

        prediction_error = (
            round(
                abs(
                    next_ticket.actual_wait_minutes - next_ticket.predicted_wait_minutes
                ),
                2,
            )
            if next_ticket.actual_wait_minutes is not None
            else None
        )

        return Response(
            {
                "status": "success",
                "called_ticket": next_ticket.ticket_number,
                "service": next_ticket.service.code,
                "counter": counter.counter_number,
                "actual_wait_minutes": next_ticket.actual_wait_minutes,
                "predicted_wait_minutes": next_ticket.predicted_wait_minutes,
                "prediction_error_minutes": prediction_error,
            },
            status=status.HTTP_200_OK,
        )
