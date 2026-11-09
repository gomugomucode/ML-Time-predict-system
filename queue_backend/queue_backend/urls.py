"""
URL configuration for queue_backend project.
"""

from api.views import PredictWaitTimeView
from django.contrib import admin
from django.urls import include, path
from api.views import ApiRootView

urlpatterns = [
    path("", ApiRootView.as_view(), name="root_index"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/predict/", PredictWaitTimeView.as_view(), name="predict_wait_time"),
]
