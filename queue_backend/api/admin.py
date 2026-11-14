from django.contrib import admin
from .models import Counter, PredictionLog, Service, Ticket


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = (
        "counter_number",
        "name",
        "is_open",
        "current_staff_name",
        "updated_at",
    )
    list_filter = ("is_open",)
    search_fields = ("name", "current_staff_name")


class PredictionLogInLine(admin.TabularInline):
    model = PredictionLog
    extra = 0
    readonly_fields = (
        "predicted_wait_minutes",
        "baseline_ast_minutes",
        "actual_wait_minutes",
        "prediction_error_minutes",
        "engine_used",
        "inference_latency_ms",
        "created_at",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "service",
        "counter",
        "status",
        "queue_length_at_arrival",
        "predicted_wait_minutes",
        "actual_wait_minutes",
        "created_at",
    )
    list_filter = ("status", "service", "created_at")
    search_fields = ("ticket_number",)
    inlines = [PredictionLogInLine]


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "predicted_wait_minutes",
        "baseline_ast_minutes",
        "actual_wait_minutes",
        "prediction_error_minutes",
        "engine_used",
        "inference_latency_ms",
        "created_at",
    )
    list_filter = ("engine_used", "created_at")
    search_fields = ("ticket__ticket_number",)
