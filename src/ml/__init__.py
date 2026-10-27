"""
Machine Learning module for SwingBot.
Contains dataset builders, training pipelines, and evaluation utilities.
"""

def __getattr__(name: str):
    if name in ("DatasetBuilder", "WarmUpPolicy", "generate_sample_labeled_dataset"):
        from src.ml.dataset_builder import (
            DatasetBuilder,
            WarmUpPolicy,
            generate_sample_labeled_dataset,
        )
        globals()["DatasetBuilder"] = DatasetBuilder
        globals()["WarmUpPolicy"] = WarmUpPolicy
        globals()["generate_sample_labeled_dataset"] = generate_sample_labeled_dataset
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["DatasetBuilder", "WarmUpPolicy", "generate_sample_labeled_dataset"]
