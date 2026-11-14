from django.urls import path
from api.views import (
    ApiRootView,
    CallNextTicketView,
    IssueTicketView,
    PredictWaitTimeView,
)

urlpatterns = [
    path("", ApiRootView.as_view(), name="api_root"),
    path("predict/", PredictWaitTimeView.as_view(), name="predict_wait_time"),
    path("tickets/issue/", IssueTicketView.as_view(), name="issue_ticket"),
    path(
        "tickets/call/<int:counter_id>/",
        CallNextTicketView.as_view(),
        name="call_ticket",
    ),
    path(
        "counters/<int:counter_id>/call-next/",
        CallNextTicketView.as_view(),
        name="call_next_ticket",
    ),
]
