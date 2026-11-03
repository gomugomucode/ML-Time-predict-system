from django.urls import path
from views import ApiRootView, PredictWaitTimeView

urlpatterns = [
    path("", ApiRootView.as_view(), name="api_root"),
    path("predict/", PredictWaitTimeView.as_view(), name="predict_wait_time"),
]
