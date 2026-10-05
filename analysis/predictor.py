"""Intelligent compression algorithm predictor and decision engine.

Analyzes input characteristics (entropy, repetition metrics, frequency skewness, file size)
to predict the optimal compression strategy before executing the algorithms.

Provides:
- Qualitative rating (High / Moderate / Low) for entropy, repetition, and skew
- Estimated compression benefit
- Recommended strategy: RLE, HUFFMAN, HYBRID, or NONE (incompressible)
- Configurable multi-objective cost evaluation (size, time, memory)
- Transparent, explainable decision rationales for academic defense
"""

from dataclasses import dataclass
from typing import Dict, Optional
from .repetition import RepetitionStats
from .statistics import DataStats


@dataclass
class CostWeights:
    """Weights for the multi-criteria decision function. Must sum to 1.0."""
    weight_size: float = 0.70  # Compression efficiency (primary goal)
    weight_time: float = 0.20  # Computational latency
    weight_memory: float = 0.10  # Working memory footprint


@dataclass
class PredictionResult:
    """Encapsulates predictive analysis output."""
    recommended_strategy: str  # 'RLE', 'HUFFMAN', 'HYBRID', 'NONE'
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    expected_benefit: str  # 'HIGH', 'MODERATE', 'LOW', 'NEGLIGIBLE'
    repetition_level: str  # 'HIGH', 'MODERATE', 'LOW'
    entropy_level: str  # 'HIGH', 'MODERATE', 'LOW'
    skew_level: str  # 'HIGH', 'MODERATE', 'LOW'
    estimated_ratio: float  # Estimated theoretical ratio (>= 1.0)
    explanation: str


class CompressionPredictor:
    """Intelligent decision engine for selecting compression algorithms."""

    def __init__(self, weights: Optional[CostWeights] = None):
        self.weights = weights or CostWeights()

    def predict(self, stats: DataStats, rep_stats: RepetitionStats) -> PredictionResult:
        """Predict the most suitable compression algorithm based on extracted features.

        Args:
            stats: General statistical characteristics.
            rep_stats: Repetition and run-length statistics.

        Returns:
            PredictionResult with detailed categorization and explainable rationale.
        """
        # Categorize Repetition
        if rep_stats.average_run_length >= 2.5 or rep_stats.repetition_percentage >= 45.0:
            repetition_level = "HIGH"
        elif rep_stats.average_run_length >= 1.6 or rep_stats.repetition_percentage >= 20.0:
            repetition_level = "MODERATE"
        else:
            repetition_level = "LOW"

        # Categorize Entropy (bits/symbol, max 8.0)
        if stats.entropy < 4.5:
            entropy_level = "LOW"
        elif stats.entropy < 6.8:
            entropy_level = "MODERATE"
        else:
            entropy_level = "HIGH"

        # Categorize Frequency Skew (Gini coefficient, 0 to 1)
        if stats.gini_coefficient > 0.50 or stats.entropy < 4.0:
            skew_level = "HIGH"
        elif stats.gini_coefficient > 0.25:
            skew_level = "MODERATE"
        else:
            skew_level = "LOW"

        # Theoretical upper bound ratio from Shannon entropy (for 8-bit symbols)
        if stats.entropy > 0:
            theoretical_ratio = round(8.0 / stats.entropy, 2)
        else:
            theoretical_ratio = 8.0

        # Decision Logic with Detailed Rationale
        reasons = []

        # Case 1: Incompressible / High-entropy random data
        if entropy_level == "HIGH" and repetition_level == "LOW" and stats.unique_symbols > 200:
            strategy = "NONE"
            benefit = "NEGLIGIBLE"
            confidence = "HIGH"
            reasons.append(
                f"Data exhibits near-maximum Shannon entropy ({stats.entropy:.2f} bits/symbol) "
                f"with negligible repetition ({rep_stats.repetition_percentage:.1f}%) and near-uniform distribution. "
                "Applying compression will likely cause file expansion due to metadata overhead."
            )

        # Case 2: Highly repetitive data
        elif repetition_level == "HIGH":
            # Check if intermediate RLE stream will benefit further from Huffman
            if skew_level == "HIGH" or stats.unique_symbols > 2:
                strategy = "HYBRID"
                benefit = "HIGH"
                confidence = "HIGH"
                reasons.append(
                    f"Substantial run repetitions detected (avg run length: {rep_stats.average_run_length:.2f}, "
                    f"{rep_stats.repetition_percentage:.1f}% repeated symbols). "
                    "Stage 1 RLE will compress runs into (count, symbol) pairs, and Stage 2 Huffman "
                    "will exploit the remaining non-uniform token frequencies for maximal compactness."
                )
            else:
                # E.g. purely AAAAAAABBBBBBB with 2 symbols
                strategy = "RLE"
                benefit = "HIGH"
                confidence = "HIGH"
                reasons.append(
                    f"Dominant run-length redundancy detected (avg run length: {rep_stats.average_run_length:.2f}). "
                    "Pure RLE offers optimal computational speed and compression ratio without Huffman tree overhead."
                )

        # Case 3: Low repetition, but skewed symbol distribution (Natural text, logs, code)
        elif skew_level in ("HIGH", "MODERATE") and repetition_level == "LOW":
            strategy = "HUFFMAN"
            benefit = "HIGH" if entropy_level == "LOW" else "MODERATE"
            confidence = "HIGH" if skew_level == "HIGH" else "MEDIUM"
            reasons.append(
                f"Low run repetition (avg run {rep_stats.average_run_length:.2f}) indicates RLE will increase size. "
                f"However, significant frequency skew (Gini {stats.gini_coefficient:.2f}, entropy {stats.entropy:.2f}) "
                "allows Huffman coding to allocate short prefix codes to frequent symbols, yielding effective compression."
            )

        # Case 4: Moderate repetition and moderate entropy
        elif repetition_level == "MODERATE":
            # Compare estimated cost
            strategy = "HYBRID"
            benefit = "MODERATE"
            confidence = "MEDIUM"
            reasons.append(
                f"Moderate run repetition ({rep_stats.repetition_percentage:.1f}%) and moderate entropy ({stats.entropy:.2f}) "
                "suggest a two-stage hybrid approach will yield superior space savings compared to single algorithms."
            )

        # Default fallback
        else:
            strategy = "HUFFMAN"
            benefit = "LOW"
            confidence = "LOW"
            reasons.append(
                "Data has balanced properties. Huffman coding is selected as the safest conservative general-purpose baseline."
            )

        explanation_text = " ".join(reasons)

        return PredictionResult(
            recommended_strategy=strategy,
            confidence=confidence,
            expected_benefit=benefit,
            repetition_level=repetition_level,
            entropy_level=entropy_level,
            skew_level=skew_level,
            estimated_ratio=theoretical_ratio,
            explanation=explanation_text,
        )
