from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from api.models import Counter, PredictionLog, Service, Ticket


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
        "model_version",
        "queue_length",
        "hour_of_day",
        "predicted_wait_minutes",
        "actual_wait_minutes",
        "absolute_error",
        "squared_error",
        "created_at",
        "resolved_at",
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "service",
        "status",
        "queue_length_at_arrival",
        "predicted_wait_minutes",
        "actual_wait_minutes",
        "counter",
        "created_at",
    )
    list_filter = ("status", "service")
    search_fields = ("ticket_number",)
    ordering = ("-created_at",)
    inlines = [PredictionLogInLine]


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "model_version",
        "queue_length",
        "hour_of_day",
        "predicted_wait_minutes",
        "actual_wait_minutes",
        "error_display",
        "created_at",
    )
    list_filter = ("model_version", "created_at")
    search_fields = ("ticket__ticket_number",)
    ordering = ("-created_at",)

    @admin.display(description="Prediction Error")
    def error_display(self, obj: PredictionLog):
        if obj.absolute_error is None:
            return mark_safe(
                '<span style="color: #6c757d; font-style: italic;">Waiting Call</span>'
            )
        # Color-code errors: Green <= 5m, Yellow 5-10m, Red > 10m
        color = (
            "#28a745"
            if obj.absolute_error <= 5.0
            else ("#e0a800" if obj.absolute_error <= 10.0 else "#dc3545")
        )
        return format_html(
            '<b style="color: {};">±{} min</b>', color, obj.absolute_error
        )
