from __future__ import annotations

from typing import Optional
from django.db import models
from django.utils import timezone


class Service(models.Model):
    """
    Represents a specific category of service offered at the facility.
    Examples: 'Accounts / Tuition Fee' (ACC), 'Admissions' (ADM), 'Examinations' (EXM).
    """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Counter(models.Model):
    """
    Represents a physical or virtual service desk/teller window.
    Tracks whether the counter is currently staffed and accepting tickets.
    """

    counter_number = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, blank=True, default="")
    is_open = models.BooleanField(default=True)
    current_staff_name = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["counter_number"]
        verbose_name = "Counter"
        verbose_name_plural = "Counters"

    def __str__(self) -> str:
        staff_str = f" ({self.current_staff_name})" if self.current_staff_name else ""
        status_str = "Open" if self.is_open else "Closed"
        return f"Counter {self.counter_number} [{status_str}]{staff_str}"


class Ticket(models.Model):
    """
    Represents a customer's queue token withdrawn at the kiosk.
    Stores the queue depth at arrival epoch t_A, the ML estimated wait time,
    and records the ground-truth actual wait time when the customer is called.
    """

    STATUS_CHOICES = [
        ("waiting", "Waiting in Line"),
        ("in_service", "Currently Being Served"),
        ("completed", "Service Completed"),
        ("cancelled", "Cancelled / No Show"),
    ]

    ticket_number = models.CharField(max_length=30, unique=True)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="tickets"
    )
    counter = models.ForeignKey(
        Counter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )

    # Queue state and predictions captured at arrival epoch t_A
    queue_length_at_arrival = models.IntegerField(default=0)
    predicted_wait_minutes = models.FloatField(default=0.0)
    prediction_engine = models.CharField(
        max_length=50, default="RandomForestRegressor"
    )

    # Realized operational outcome
    actual_wait_minutes = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="waiting"
    )

    # Epoch timestamps (t_A, t_S, t_D)
    created_at = models.DateTimeField(auto_now_add=True)  # Arrival epoch t_A
    called_at = models.DateTimeField(null=True, blank=True)  # Service start epoch t_S
    completed_at = models.DateTimeField(null=True, blank=True)  # Service end epoch t_D

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["service", "status"]),
        ]

    def mark_as_called(self, counter: Counter) -> None:
        """
        Marks ticket as called to a teller counter and computes actual wait time W_q = t_S - t_A.
        Also synchronizes the prediction error on linked PredictionLog records.
        """
        self.status = "in_service"
        self.counter = counter
        self.called_at = timezone.now()

        # Calculate actual waiting duration in minutes
        wait_seconds = (self.called_at - self.created_at).total_seconds()
        self.actual_wait_minutes = round(max(0.0, wait_seconds / 60.0), 2)
        self.save()

        # Update linked prediction log if exists
        for log in self.prediction_logs.all():
            log.actual_wait_minutes = self.actual_wait_minutes
            log.prediction_error_minutes = round(
                abs(log.predicted_wait_minutes - self.actual_wait_minutes), 2
            )
            log.save()

    def mark_as_completed(self) -> None:
        """Marks the ticket service as completed."""
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def mark_as_cancelled(self) -> None:
        """Marks the ticket as cancelled or no-show."""
        self.status = "cancelled"
        self.save()

    def __str__(self) -> str:
        return f"{self.ticket_number} - {self.service.code} [{self.get_status_display()}]"


class PredictionLog(models.Model):
    """
    Immutable audit log storing every prediction generated by the ML or fallback engine.
    Used for monitoring model drift, evaluating live MAE, and auditing queue SLAs.
    """

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="prediction_logs"
    )
    predicted_wait_minutes = models.FloatField()
    baseline_ast_minutes = models.FloatField(null=True, blank=True)
    actual_wait_minutes = models.FloatField(null=True, blank=True)
    prediction_error_minutes = models.FloatField(null=True, blank=True)
    engine_used = models.CharField(max_length=50, default="RandomForestRegressor")
    inference_latency_ms = models.FloatField(default=0.0)
    features_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prediction Log"
        verbose_name_plural = "Prediction Logs"
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["engine_used"]),
        ]

    def __str__(self) -> str:
        err_str = (
            f" (Err: {self.prediction_error_minutes:.2f}m)"
            if self.prediction_error_minutes is not None
            else ""
        )
        return (
            f"Prediction #{self.pk} for {self.ticket.ticket_number}: "
            f"{self.predicted_wait_minutes:.1f}m via {self.engine_used}{err_str}"
        )
