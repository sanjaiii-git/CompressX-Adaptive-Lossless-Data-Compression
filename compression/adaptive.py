"""Adaptive intelligent compression engine.

Combines data analysis, predictive modeling, multi-criteria cost scoring,
and container packaging into a unified interface.

Supports two operational selection paradigms:
1. Prediction-Based Selection: Selects strategy based purely on pre-compression statistical features.
2. Performance-Based Selection: Benchmarks all candidate strategies and chooses the optimal cost trade-off.
"""

import hashlib
import time
from typing import Any, Dict, Optional, Tuple, Union

from analysis.entropy import calculate_entropy
from analysis.repetition import analyze_repetition
from analysis.statistics import calculate_statistics
from analysis.predictor import CompressionPredictor, CostWeights, PredictionResult
from storage.container import Container, CompressedPackage
from storage.metadata import Metadata
from .rle import RLECompressor
from .huffman import HuffmanCompressor
from .hybrid import HybridCompressor


class AdaptiveCompressor:
    """Orchestrates adaptive strategy selection, compression, and verification."""

    def __init__(self, weights: Optional[CostWeights] = None):
        self.weights = weights or CostWeights()
        self.predictor = CompressionPredictor(weights=self.weights)

    def analyze(self, data: bytes) -> Tuple[Dict[str, Any], PredictionResult]:
        """Analyze data characteristics and return statistical profile and prediction."""
        entropy_val = calculate_entropy(data)
        rep_stats = analyze_repetition(data)
        data_stats = calculate_statistics(data, entropy_val)
        prediction = self.predictor.predict(data_stats, rep_stats)

        profile = {
            "size_bytes": len(data),
            "entropy": entropy_val,
            "unique_symbols": data_stats.unique_symbols,
            "total_runs": rep_stats.total_runs,
            "average_run_length": rep_stats.average_run_length,
            "max_run_length": rep_stats.max_run_length,
            "repetition_percentage": rep_stats.repetition_percentage,
            "gini_coefficient": data_stats.gini_coefficient,
            "is_skewed": data_stats.is_skewed,
            "most_frequent": data_stats.most_frequent,
            "least_frequent": data_stats.least_frequent,
        }
        return profile, prediction

    def _compress_with_strategy(
        self, strategy: str, data: bytes, file_name: str = ""
    ) -> Tuple[bytes, Metadata]:
        """Compress data using a specific strategy and prepare container metadata."""
        strategy = strategy.upper()

        if strategy == "RLE":
            payload = RLECompressor.compress(data)
            meta = Metadata(file_name=file_name)
            return payload, meta

        elif strategy == "HUFFMAN":
            payload, freqs, pad = HuffmanCompressor.compress(data)
            str_freqs = {str(k): v for k, v in freqs.items()}
            meta = Metadata(
                file_name=file_name,
                padding_bits=pad,
                frequencies=str_freqs,
            )
            return payload, meta

        elif strategy == "HYBRID":
            payload, freqs, pad, inter_size = HybridCompressor.compress(data)
            str_freqs = {str(k): v for k, v in freqs.items()}
            meta = Metadata(
                file_name=file_name,
                padding_bits=pad,
                intermediate_size=inter_size,
                frequencies=str_freqs,
            )
            return payload, meta

        else:
            # Fallback / None: store raw data
            meta = Metadata(file_name=file_name)
            return data, meta

    def compress_adaptive(
        self,
        data: bytes,
        file_name: str = "",
        selection_mode: str = "prediction",
    ) -> Tuple[bytes, str, PredictionResult, Dict[str, Any]]:
        """Compress data adaptively, selecting either via prediction or actual evaluation.

        Args:
            data: Input raw bytes.
            file_name: Source file name.
            selection_mode: 'prediction' (heuristic-based) or 'evaluate_all' (benchmark-based).

        Returns:
            Tuple of:
            - container_bytes: Packaged .ahdc archive bytes
            - selected_strategy: Algorithm chosen
            - prediction: PredictionResult object
            - execution_details: Timing and size dictionary
        """
        start_time = time.perf_counter()
        profile, prediction = self.analyze(data)

        if selection_mode == "evaluate_all":
            # Test RLE, Huffman, and Hybrid to select the optimal strategy
            results = {}
            for strat in ["RLE", "HUFFMAN", "HYBRID"]:
                t0 = time.perf_counter()
                payload, meta = self._compress_with_strategy(strat, data, file_name)
                t_enc = time.perf_counter() - t0
                results[strat] = {
                    "payload": payload,
                    "meta": meta,
                    "size": len(payload),
                    "enc_time": t_enc,
                }

            # If compression doesn't beat original size and prediction is NONE, allow NONE
            min_size = min(res["size"] for res in results.values())
            if min_size >= len(data) and prediction.recommended_strategy == "NONE":
                selected_strategy = "NONE"
                payload = data
                meta = Metadata(file_name=file_name)
            else:
                # Rank according to cost function
                # Normalize size and time
                orig_sz = max(len(data), 1)
                max_time = max(max(r["enc_time"] for r in results.values()), 1e-6)

                best_cost = float("inf")
                selected_strategy = "HUFFMAN"
                for strat, res in results.items():
                    norm_sz = res["size"] / orig_sz
                    norm_tm = res["enc_time"] / max_time
                    cost = (self.weights.weight_size * norm_sz) + (self.weights.weight_time * norm_tm)
                    if cost < best_cost:
                        best_cost = cost
                        selected_strategy = strat

                payload = results[selected_strategy]["payload"]
                meta = results[selected_strategy]["meta"]

        else:
            # Prediction-based selection
            selected_strategy = prediction.recommended_strategy
            if selected_strategy == "NONE":
                # Data is incompressible; store as NONE (raw payload) to prevent bloat
                payload = data
                meta = Metadata(file_name=file_name)
            else:
                payload, meta = self._compress_with_strategy(selected_strategy, data, file_name)

        # Pack into container
        container_bytes = Container.pack(selected_strategy, payload, data, meta)
        total_time = time.perf_counter() - start_time

        details = {
            "selected_strategy": selected_strategy,
            "predicted_strategy": prediction.recommended_strategy,
            "prediction_accurate": (
                selected_strategy == prediction.recommended_strategy
                or (selected_strategy in ("RLE", "HYBRID") and prediction.recommended_strategy in ("RLE", "HYBRID"))
            ),
            "original_size": len(data),
            "payload_size": len(payload),
            "container_size": len(container_bytes),
            "compression_ratio": round(len(data) / len(container_bytes), 3) if len(container_bytes) > 0 else 0.0,
            "space_saving_pct": round(((len(data) - len(container_bytes)) / max(len(data), 1)) * 100, 2),
            "total_elapsed_time": round(total_time, 4),
            "profile": profile,
        }

        return container_bytes, selected_strategy, prediction, details

    @classmethod
    def decompress_container(
        cls, container_bytes: bytes
    ) -> Tuple[bytes, bool, str, Dict[str, Any]]:
        """Decompress an .ahdc container and verify lossless integrity.

        Args:
            container_bytes: Packed .ahdc container bytes.

        Returns:
            Tuple of:
            - decompressed_bytes: Restored original bytes
            - integrity_passed: Boolean indicating exact hash match
            - message: Verification status message
            - metadata_info: Container attributes dictionary
        """
        start_time = time.perf_counter()
        pkg = Container.unpack(container_bytes)

        strategy = pkg.algorithm_name.upper()
        payload = pkg.payload
        meta = pkg.metadata

        if strategy == "RLE":
            decompressed = RLECompressor.decompress(payload)

        elif strategy == "HUFFMAN":
            int_freqs = meta.get_int_frequencies()
            decompressed = HuffmanCompressor.decompress(
                payload, int_freqs, meta.padding_bits, original_size=pkg.original_size
            )

        elif strategy == "HYBRID":
            int_freqs = meta.get_int_frequencies()
            decompressed = HybridCompressor.decompress(
                payload, int_freqs, meta.padding_bits, intermediate_size=meta.intermediate_size
            )

        elif strategy == "NONE":
            decompressed = payload

        else:
            raise ValueError(f"Unknown compression algorithm in archive: {strategy}")

        dec_time = time.perf_counter() - start_time

        # Verify integrity
        computed_sha256 = hashlib.sha256(decompressed).hexdigest()
        integrity_passed = (computed_sha256.lower() == pkg.original_sha256.lower()) and (
            len(decompressed) == pkg.original_size
        )

        status_msg = (
            f"Integrity Check: PASSED (SHA-256 match, {len(decompressed)} bytes verified)"
            if integrity_passed
            else f"Integrity Check: FAILED (Hash mismatch! Expected {pkg.original_sha256[:12]}..., got {computed_sha256[:12]}...)"
        )

        info = {
            "algorithm": strategy,
            "original_size": pkg.original_size,
            "decompressed_size": len(decompressed),
            "decoding_time": round(dec_time, 4),
            "expected_sha256": pkg.original_sha256,
            "computed_sha256": computed_sha256,
            "file_name": meta.file_name,
        }

        return decompressed, integrity_passed, status_msg, info
