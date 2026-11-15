from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
