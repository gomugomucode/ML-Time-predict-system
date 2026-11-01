from django.urls import path
from .views import PredictWaitTimeView

urlpatterns = [
    path("predict/", PredictWaitTimeView.as_view(), name="predict_wait_time"),
]
