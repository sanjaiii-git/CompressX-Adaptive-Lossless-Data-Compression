"""Evaluation package for performance measurement, metrics computation, and benchmarking."""

from .metrics import calculate_metrics, CompressionMetrics, verify_integrity
from .benchmark import BenchmarkRunner

__all__ = ["calculate_metrics", "CompressionMetrics", "verify_integrity", "BenchmarkRunner"]
