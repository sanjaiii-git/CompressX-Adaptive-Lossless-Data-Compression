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

    ALL_CANDIDATES = ["RLE", "HYBRID", "DEFLATE", "LZ77", "LZW", "HUFFMAN", "BWT"]

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
        if rep_stats.average_run_length >= 2.0 or rep_stats.repetition_percentage >= 35.0 or rep_stats.is_rle_promising:
            repetition_level = "HIGH"
        elif rep_stats.average_run_length >= 1.4 or rep_stats.repetition_percentage >= 15.0:
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
            candidates = ["DEFLATE", "HUFFMAN", "RLE"]
            benefit = "NEGLIGIBLE"
            confidence = "HIGH"
            reasons.append(
                f"Data exhibits near-maximum Shannon entropy ({stats.entropy:.2f} bits/symbol) "
                f"with negligible repetition ({rep_stats.repetition_percentage:.1f}%) and near-uniform distribution. "
                "Applying compression will likely cause file expansion due to metadata overhead."
            )

        # Case 2: Pure single-symbol repetition (e.g. 'aaaa...')
        elif stats.unique_symbols == 1:
            strategy = "RLE"
            candidates = ["RLE", "HYBRID", "DEFLATE", "LZ77"]
            benefit = "HIGH"
            confidence = "HIGH"
            reasons.append(
                f"Pure single-symbol sequence detected ({stats.unique_symbols} unique byte value, "
                f"avg run length {rep_stats.average_run_length:.1f}). "
                "RLE collapses continuous runs directly into minimal length tokens without dictionary overhead."
            )

        # Case 3: Highly repetitive data or long runs
        elif repetition_level == "HIGH" or rep_stats.is_rle_promising:
            if rep_stats.average_run_length >= 3.0:
                strategy = "RLE"
                candidates = ["RLE", "HYBRID", "DEFLATE", "LZ77", "LZW"]
            else:
                strategy = "HYBRID"
                candidates = ["HYBRID", "RLE", "DEFLATE", "LZ77", "LZW"]
            benefit = "HIGH"
            confidence = "HIGH"
            reasons.append(
                f"High run-length repetition detected (avg run length: {rep_stats.average_run_length:.2f}, "
                f"{rep_stats.repetition_percentage:.1f}% repeated bytes). "
                "Run-Length Encoding and Two-Stage Hybrid compression are the primary candidates for run collapsing."
            )

        # Case 4: High skewness without long runs (natural language, code, structured tables)
        elif skew_level == "HIGH" and repetition_level == "LOW":
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "HUFFMAN", "LZ77", "LZW", "RLE"]
            benefit = "HIGH"
            confidence = "HIGH"
            reasons.append(
                f"Highly non-uniform symbol frequencies (Gini: {stats.gini_coefficient:.2f}) with minimal run repetition. "
                "DEFLATE combines LZ77 substring dictionary matching with Huffman prefix coding for optimal ratio."
            )

        # Case 5: Moderate entropy and repetition
        elif entropy_level == "MODERATE":
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "HYBRID", "LZ77", "LZW", "HUFFMAN", "RLE"]
            benefit = "MODERATE"
            confidence = "MEDIUM"
            reasons.append(
                f"Moderate Shannon entropy ({stats.entropy:.2f} bits/symbol) with moderate frequency skew. "
                "Evaluating dictionary and run-length candidates to capture recurring patterns."
            )

        # Case 6: Default fallback
        else:
            strategy = "DEFLATE"
            candidates = ["DEFLATE", "HUFFMAN", "RLE", "LZW", "HYBRID"]
            benefit = "MODERATE"
            confidence = "MEDIUM"
            reasons.append(
                "Balanced data profile. Evaluating all compression candidates to determine the optimal trade-off."
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
            best_expanding_cand = min(valid_candidates.keys(), key=lambda k: valid_candidates[k]["final_stored_size"])
            return "NONE", (
                f"All evaluated compression algorithms caused storage expansion "
                f"(smallest candidate was {best_expanding_cand} with {min_stored_size:,} bytes vs {original_size:,} bytes original). "
                f"Raw Bypass selected to prevent archive bloat."
            )

        # Filter strictly to candidates achieving real positive compression
        compressing_candidates = {
            k: v for k, v in valid_candidates.items()
            if v["final_stored_size"] < original_size
        }

        if not compressing_candidates:
            return "NONE", "No algorithm achieved positive compression; Raw Bypass selected."

        obj = objective.lower().replace(" ", "_")

        # Candidate with strictly smallest final stored size (and tie-breaker on time)
        min_size_alg = min(
            compressing_candidates.keys(),
            key=lambda k: (compressing_candidates[k]["final_stored_size"], compressing_candidates[k]["encoding_time"])
        )
        min_size = compressing_candidates[min_size_alg]["final_stored_size"]
        min_saving = compressing_candidates[min_size_alg]["space_saving_pct"]

        if "max" in obj:
            # Objective 1: Maximum Compression (strictly smallest final stored size)
            rationale = (
                f"Selected under 'Maximum Compression' objective: {min_size_alg} produced the smallest final container "
                f"({min_size:,} bytes, {min_saving:.1f}% space saved)."
            )
            return min_size_alg, rationale

        elif "fast" in obj or "speed" in obj:
            # Objective 2: Fast Compression (fastest encoding time among candidates achieving positive compression)
            fastest_alg = min(compressing_candidates.keys(), key=lambda k: compressing_candidates[k]["encoding_time"])
            fastest_time = compressing_candidates[fastest_alg]["encoding_time"]
            fastest_saving = compressing_candidates[fastest_alg]["space_saving_pct"]
            rationale = (
                f"Selected under 'Fast Compression' objective: {fastest_alg} achieved positive compression "
                f"({fastest_saving:.1f}% space saved) with the lowest encoding latency ({fastest_time:.5f}s)."
            )
            return fastest_alg, rationale

        else:
            # Objective 3: Balanced (Transparent Multi-Criteria Cost Function)
            # Size penalty dominates (85% weight) so that speed cannot override a genuinely smaller output.
            # Speed penalty (15% weight) serves to break ties or select faster options when sizes are within ~2%.
            max_size = max(v["final_stored_size"] for v in compressing_candidates.values())
            size_span = max(max_size - min_size, 1)

            min_time = min(v["encoding_time"] for v in compressing_candidates.values())
            max_time = max(v["encoding_time"] for v in compressing_candidates.values())
            time_span = max(max_time - min_time, 1e-9)

            best_cost = float("inf")
            best_alg = min_size_alg  # Frontrunner defaults to the candidate with the smallest stored size

            for alg, metrics in compressing_candidates.items():
                norm_size = (metrics["final_stored_size"] - min_size) / size_span
                norm_time = (metrics["encoding_time"] - min_time) / time_span
                cost = (0.85 * norm_size) + (0.15 * norm_time)
                if cost < best_cost - 1e-7:
                    best_cost = cost
                    best_alg = alg

            best_size = compressing_candidates[best_alg]["final_stored_size"]
            best_saving = compressing_candidates[best_alg]["space_saving_pct"]
            best_time = compressing_candidates[best_alg]["encoding_time"]
            rationale = (
                f"Selected under 'Balanced' objective: {best_alg} offered the optimal multi-criteria trade-off "
                f"({best_saving:.1f}% space saved, {best_size:,} bytes stored, {best_time:.5f}s latency; "
                f"formula: 0.85*size_norm + 0.15*time_norm)."
            )
            return best_alg, rationale
