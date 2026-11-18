from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from api.ml_service import WaitTimePredictor
from api.ml_trainer import train_and_save_model


class Command(BaseCommand):
    help = (
        "Train the RandomForestRegressor wait-time prediction model from CSV "
        "datasets, evaluate metrics, save wait_time_rf_model.joblib inside "
        "queue_backend/api/, and refresh the in-memory predictor."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--data-dir",
            type=str,
            default=None,
            help="Optional custom path to directory containing queue CSV datasets.",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Optional output path for wait_time_rf_model.joblib.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.NOTICE("Starting ML queue wait-time model training pipeline...")
        )

        _, metrics, saved_path = train_and_save_model(
            data_path=options.get("data_dir"),
            output_path=options.get("output"),
            verbose=True,
        )

        # Hot-reload singleton if already instantiated
        if WaitTimePredictor._instance is not None:
            WaitTimePredictor._instance.load_model(auto_train=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Training complete! Saved to {saved_path} "
                f"(MAE: {metrics['mae']:.2f} min, R2: {metrics['r2']:.4f}, "
                f"Improvement: +{metrics['improvement_pct']:.2f}% over baseline)."
            )
        )
