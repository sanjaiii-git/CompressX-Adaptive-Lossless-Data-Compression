"""Intelligent compression algorithm predictor and decision engine.

Analyzes input characteristics (entropy, repetition metrics, frequency skewness, file size)
to predict suitable compression strategies before or during algorithm execution.

Supports 3 configurable selection objectives:
- 'max_compression': Strictly prioritizes smallest final stored size.
- 'balanced': Multi-criteria cost function balancing size, encoding latency, and memory.
- 'fast': Prioritizes encoding throughput while avoiding file expansion.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from .repetition import RepetitionStats
from .statistics import DataStats


@dataclass
class CostWeights:
    """Weights for the multi-criteria decision function. Must sum to 1.0."""
    weight_size: float = 0.65     # Compression efficiency / size reduction
    weight_time: float = 0.25     # Encoding latency / throughput
    weight_memory: float = 0.10   # Working memory footprint

    @classmethod
    def for_objective(cls, objective: str = "balanced") -> "CostWeights":
        """Factory method to get pre-tuned weights for specific objectives."""
        obj = objective.lower().replace(" ", "_")
        if "max" in obj:
            return cls(weight_size=1.00, weight_time=0.00, weight_memory=0.00)
        elif "fast" in obj or "speed" in obj:
            return cls(weight_size=0.20, weight_time=0.70, weight_memory=0.10)
        else:  # balanced
            return cls(weight_size=0.65, weight_time=0.25, weight_memory=0.10)


@dataclass
class PredictionResult:
    """Encapsulates predictive analysis output and candidate recommendations."""
    recommended_strategy: str      # e.g. 'DEFLATE', 'HUFFMAN', 'RLE', 'HYBRID', 'LZ77', 'LZW', 'BWT', 'NONE'
    candidate_algorithms: List[str] # Recommended candidate subset to evaluate
    confidence: str                # 'HIGH', 'MEDIUM', 'LOW'
    expected_benefit: str          # 'HIGH', 'MODERATE', 'LOW', 'NEGLIGIBLE'
    repetition_level: str          # 'HIGH', 'MODERATE', 'LOW'
    entropy_level: str             # 'HIGH', 'MODERATE', 'LOW'
    skew_level: str                # 'HIGH', 'MODERATE', 'LOW'
    estimated_ratio: float         # Estimated theoretical ratio bound (>= 1.0)
    explanation: str


class CompressionPredictor:
    """Intelligent decision engine for selecting compression algorithms."""

    ALL_CANDIDATES = ["DEFLATE", "HUFFMAN", "LZ77", "LZW", "HYBRID", "RLE", "BWT"]

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

        reasons = []

        # Case 1: Incompressible / High-entropy random or pre-encrypted data
        if entropy_level == "HIGH" and repetition_level == "LOW" and stats.unique_symbols > 200:
            strategy = "NONE"
            candidates = ["DEFLATE", "HUFFMAN"]
            benefit = "NEGLIGIBLE"
            confidence = "HIGH"
            reasons.append(
                f"Data exhibits near-maximum Shannon entropy ({stats.entropy:.2f} bits/symbol) "
                f"with negligible repetition ({rep_stats.repetition_percentage:.1f}%) and near-uniform distribution. "
                "Applying compression will likely cause file expansion due to metadata overhead."
            )

        # Case 2: Highly repetitive data
        elif repetition_level == "HIGH":
            if stats.unique_symbols == 1:
                strategy = "RLE"
                candidates = ["RLE", "DEFLATE", "HYBRID"]
                benefit = "HIGH"
                confidence = "HIGH"
                reasons.append(
                    f"Pure single-symbol repetition detected (avg run length: {rep_stats.average_run_length:.2f}). "
                    "RLE is optimal for this case - no frequency skew to exploit, and Huffman stage would add overhead."
                )
            elif skew_level == "HIGH" or stats.unique_symbols > 2:
                strategy = "HYBRID"
                candidates = ["HYBRID", "DEFLATE", "RLE", "LZ77"]
                benefit = "HIGH"
                confidence = "HIGH"
                reasons.append(
                    f"Substantial run repetitions detected (avg run length: {rep_stats.average_run_length:.2f}, "
                    f"{rep_stats.repetition_percentage:.1f}% repeated symbols). "
                    "Stage 1 RLE compresses runs into tokens, and Stage 2 Huffman compresses remaining non-uniform frequencies."
                )
            else:
                strategy = "RLE"
                candidates = ["RLE", "HYBRID", "DEFLATE"]
                benefit = "HIGH"
                confidence = "HIGH"
                reasons.append(
                    f"High run-length repetition with uniform symbol distribution. RLE provides linear O(N) compression."
                )

        # Case 3: High skewness without long runs (natural language, code, structured tables)
        elif skew_level == "HIGH" and repetition_level == "LOW":
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "HUFFMAN", "LZ77", "LZW"]
            benefit = "HIGH"
            confidence = "HIGH"
            reasons.append(
                f"Highly non-uniform symbol frequencies (Gini: {stats.gini_coefficient:.2f}) with minimal run repetition. "
                "DEFLATE combines LZ77 substring dictionary matching with Huffman prefix coding for optimal ratio."
            )

        # Case 4: Moderate entropy and repetition
        elif entropy_level == "MODERATE":
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "LZ77", "LZW", "HUFFMAN"]
            benefit = "MODERATE"
            confidence = "MEDIUM"
            reasons.append(
                f"Moderate Shannon entropy ({stats.entropy:.2f} bits/symbol) with moderate frequency skew. "
                "Dictionary-based algorithms (DEFLATE, LZ77, LZW) will capture recurring multi-byte phrases."
            )

        # Case 5: Default fallback
        else:
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "HUFFMAN", "LZW"]
            benefit = "MODERATE"
            confidence = "MEDIUM"
            reasons.append(
                f"Balanced data profile. Evaluating dictionary and entropy candidates to determine optimal trade-off."
            )

        return PredictionResult(
            recommended_strategy=strategy,
            candidate_algorithms=candidates,
            confidence=confidence,
            expected_benefit=benefit,
            repetition_level=repetition_level,
            entropy_level=entropy_level,
            skew_level=skew_level,
            estimated_ratio=theoretical_ratio,
            explanation=" ".join(reasons),
        )

    def select_best(
        self,
        measured_results: Dict[str, Dict[str, Any]],
        objective: str = "balanced",
        original_size: int = 1,
    ) -> Tuple[str, str]:
        """Select the best candidate algorithm based on actual measured metrics and objective.

        Args:
            measured_results: Dict mapping algorithm_name -> metrics dict with keys:
                'final_stored_size', 'encoding_time', 'integrity_passed', 'space_saving_pct'
            objective: 'max_compression', 'balanced', or 'fast'.
            original_size: Size of uncompressed input data.

        Returns:
            Tuple of (selected_strategy_name, selection_rationale).
        """
        valid_candidates = {
            k: v for k, v in measured_results.items()
            if v.get("integrity_passed", True) and v.get("final_stored_size", float("inf")) < float("inf")
        }

        if not valid_candidates:
            return "NONE", "No candidate algorithm passed integrity verification; defaulting to Raw Bypass."

        # Check if ALL algorithms caused file expansion
        min_stored_size = min(v["final_stored_size"] for v in valid_candidates.values())
        if min_stored_size >= original_size:
            return "NONE", (
                f"All evaluated compression algorithms caused storage expansion "
                f"(smallest candidate final size was {min_stored_size:,} bytes vs {original_size:,} bytes original). "
                f"Raw Bypass selected to prevent archive bloat."
            )

        obj = objective.lower().replace(" ", "_")

        if "max" in obj:
            # Objective 1: Maximum Compression (smallest final stored size)
            best_alg = min(valid_candidates.keys(), key=lambda k: valid_candidates[k]["final_stored_size"])
            best_size = valid_candidates[best_alg]["final_stored_size"]
            best_saving = valid_candidates[best_alg]["space_saving_pct"]
            rationale = (
                f"Selected under 'Maximum Compression' objective: {best_alg} produced the smallest final container "
                f"({best_size:,} bytes, {best_saving:.1f}% space saved)."
            )
            return best_alg, rationale

        elif "fast" in obj or "speed" in obj:
            # Objective 2: Fast Compression (fastest encoding time that still achieves positive compression)
            compressing_candidates = {
                k: v for k, v in valid_candidates.items()
                if v["final_stored_size"] < original_size
            }
            if not compressing_candidates:
                return "NONE", "No algorithm achieved positive compression; Raw Bypass selected."

            best_alg = min(compressing_candidates.keys(), key=lambda k: compressing_candidates[k]["encoding_time"])
            best_time = compressing_candidates[best_alg]["encoding_time"]
            best_saving = compressing_candidates[best_alg]["space_saving_pct"]
            rationale = (
                f"Selected under 'Fast Compression' objective: {best_alg} achieved positive compression "
                f"({best_saving:.1f}% space saved) with the lowest encoding latency ({best_time:.4f}s)."
            )
            return best_alg, rationale

        else:
            # Objective 3: Balanced (Multi-criteria cost function)
            weights = CostWeights.for_objective("balanced")
            max_size = max(v["final_stored_size"] for v in valid_candidates.values()) or 1
            max_time = max(v["encoding_time"] for v in valid_candidates.values()) or 1e-6

            best_cost = float("inf")
            best_alg = "DEFLATE" if "DEFLATE" in valid_candidates else list(valid_candidates.keys())[0]

            for alg, metrics in valid_candidates.items():
                norm_sz = metrics["final_stored_size"] / max_size
                norm_tm = metrics["encoding_time"] / max_time
                cost = (weights.weight_size * norm_sz) + (weights.weight_time * norm_tm)
                if cost < best_cost:
                    best_cost = cost
                    best_alg = alg

            best_size = valid_candidates[best_alg]["final_stored_size"]
            best_saving = valid_candidates[best_alg]["space_saving_pct"]
            best_time = valid_candidates[best_alg]["encoding_time"]
            rationale = (
                f"Selected under 'Balanced' objective: {best_alg} offered the optimal multi-criteria trade-off "
                f"({best_saving:.1f}% space saved in {best_time:.4f}s)."
            )
            return best_alg, rationale
