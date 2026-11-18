import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from api import ml_service
from api.ml_service import WaitTimePredictor
from api.models import Service, Counter, Ticket, PredictionLog
from api.views import get_queue_state_data, broadcast_queue_state

class QueueSystemIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.service = Service.objects.create(code="ACC", name="Tuition & Semester Fee")
        self.counter = Counter.objects.create(counter_number=1, is_open=True)

    def test_predict_endpoint(self):
        response = self.client.post("/api/predict/", {
            "queue_length": 5,
            "hour_of_day": 10,
            "day_of_week": 1,
            "is_weekend": 0,
            "active_counters": 1,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("predicted_wait_minutes", response.data)
        self.assertIn("engine", response.data)

    def test_issue_ticket_and_broadcast(self):
        response = self.client.post("/api/tickets/issue/", {
            "service_code": "ACC"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("ticket_number", response.data)
        self.assertEqual(response.data["people_ahead"], 0)
        self.assertIn("estimated_wait_minutes", response.data)

        # Verify DB records
        ticket = Ticket.objects.get(ticket_number=response.data["ticket_number"])
        self.assertEqual(ticket.status, "waiting")
        self.assertTrue(PredictionLog.objects.filter(ticket=ticket).exists())

    def test_call_next_ticket(self):
        # 1. Issue a ticket first
        self.client.post("/api/tickets/issue/", {"service_code": "ACC"}, format="json")

        # 2. Call ticket from counter 1
        response = self.client.post("/api/counters/1/call-next/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["counter"], 1)
        self.assertIsNotNone(response.data["actual_wait_minutes"])

    def test_channel_layer_state(self):
        channel_layer = get_channel_layer()
        self.assertIsNotNone(channel_layer)

        state = get_queue_state_data()
        self.assertEqual(state["type"], "QUEUE_STATE_CHANGED")
        self.assertIn("now_serving", state)
        self.assertIn("upcoming", state)
        self.assertIn("total_waiting", state)

        # Verify broadcast executes without raising errors
        broadcast_queue_state()

    def test_auto_trains_when_joblib_missing_and_matches_prediction(self):
        # Capture baseline prediction from currently loaded model
        baseline_pred = WaitTimePredictor.get_instance().predict_detailed(
            queue_length=8,
            hour_of_day=14,
            day_of_week=1,
            is_weekend=0,
            active_counters=1,
        )

        # Simulate a fresh clone with NO wait_time_rf_model.joblib present
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_model_path = Path(tmpdir) / "wait_time_rf_model.joblib"
            self.assertFalse(missing_model_path.exists())

            with patch.object(ml_service, "CANDIDATE_MODEL_PATHS", [missing_model_path]):
                fresh_predictor = WaitTimePredictor()

                # Verify auto-training created the joblib file and loaded RandomForest
                self.assertTrue(missing_model_path.exists())
                self.assertTrue(fresh_predictor.is_ready())
                self.assertEqual(fresh_predictor.model_path, missing_model_path)

                auto_pred = fresh_predictor.predict_detailed(
                    queue_length=8,
                    hour_of_day=14,
                    day_of_week=1,
                    is_weekend=0,
                    active_counters=1,
                )
                self.assertEqual(auto_pred["engine"], "RandomForestRegressor")
                self.assertEqual(
                    auto_pred["predicted_wait_time_minutes"],
                    baseline_pred["predicted_wait_time_minutes"],
                )

    def test_ast_fallback_when_model_and_auto_train_disabled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_model_path = Path(tmpdir) / "nonexistent.joblib"
            with patch.object(ml_service, "CANDIDATE_MODEL_PATHS", [missing_model_path]):
                predictor = WaitTimePredictor.__new__(WaitTimePredictor)
                predictor.model = None
                predictor.model_path = None
                predictor._is_loaded = False
                loaded = predictor.load_model(auto_train=False)

                self.assertFalse(loaded)
                self.assertFalse(predictor.is_ready())
                res = predictor.predict_detailed(
                    queue_length=10,
                    hour_of_day=12,
                    day_of_week=2,
                    is_weekend=0,
                    active_counters=2,
                )
                self.assertEqual(res["engine"], "AverageServiceTimeFallback")
                self.assertEqual(res["predicted_wait_time_minutes"], 11.9)
