"""
Models module for StockBot_Model.
Contains baseline classifiers, model training pipelines, and prediction utilities.
"""

def __getattr__(name: str):
    if name in ("BaselineMLExperiment", "compute_comprehensive_metrics"):
        from src.models.baseline_classifier import (
            BaselineMLExperiment,
            compute_comprehensive_metrics,
        )
        globals()["BaselineMLExperiment"] = BaselineMLExperiment
        globals()["compute_comprehensive_metrics"] = compute_comprehensive_metrics
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["BaselineMLExperiment", "compute_comprehensive_metrics"]
