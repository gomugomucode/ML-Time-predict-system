from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self) -> None:
        """
        Preload ML model into memory when Django server initializes.
        Ensures warm-start in-memory cache and sub-10ms inference latency.
        """
        import os
        import sys

        # Prevent double-loading in the outer watchdog process of Django runserver
        is_runserver = any("runserver" in arg for arg in sys.argv)
        is_reloader_parent = (
            is_runserver
            and "--noreload" not in sys.argv
            and os.environ.get("RUN_MAIN") != "true"
        )

        if not is_reloader_parent:
            try:
                from .ml_service import WaitTimePredictor

                predictor = WaitTimePredictor.get_instance()
                if predictor.is_ready():
                    print(
                        ">>> [ML Service] WaitTimePredictor preloaded into in-memory singleton (Ready)."
                    )
                else:
                    print(
                        ">>> [ML Service] WaitTimePredictor running in Analytical AST Fallback mode."
                    )
            except Exception as e:
                print(f">>> [ML Service] Warning during model preloading: {e}")
