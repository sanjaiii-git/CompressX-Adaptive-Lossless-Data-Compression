"""Adaptive intelligent compression engine.

Combines information-theoretic data profiling, predictive modeling, multi-criteria
cost scoring, and container packaging into a unified interface.

Supports 8 Lossless Compression Algorithms:
1. RAW (Bypass mode for incompressible streams)
2. RLE (Run-Length Encoding)
3. HUFFMAN (Canonical Huffman Prefix Coding)
4. HYBRID (Sequential Two-Stage RLE + Huffman)
5. LZ77 (Sliding-Window Dictionary Encoding)
6. DEFLATE (LZ77 + Huffman RFC 1951)
7. LZW (Lempel-Ziv-Welch Dictionary Encoding)
8. BWT (Burrows-Wheeler Transform + MTF + Zero-RLE)

Supports 3 Configurable Objectives:
- 'max_compression': Strictly prioritizes minimum stored artifact size.
- 'balanced': Multi-criteria cost optimization (size, encoding latency, memory).
- 'fast': Prioritizes encoding throughput while avoiding file expansion.
"""

import hashlib
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple, Union

from analysis.entropy import calculate_entropy
from analysis.repetition import analyze_repetition
from analysis.statistics import calculate_statistics
from analysis.predictor import CompressionPredictor, CostWeights, PredictionResult
from storage.container import Container, CompressedPackage
from storage.metadata import Metadata
try:
    from .rle import RLECompressor
    from .huffman import HuffmanCompressor
    from .hybrid import HybridCompressor
    from .lz77 import LZ77Compressor
    from .deflate import DeflateCompressor
    from .lzw import LZWCompressor
    from .bwt import BWTCompressor
except (ImportError, ValueError):
    from compression.rle import RLECompressor
    from compression.huffman import HuffmanCompressor
    from compression.hybrid import HybridCompressor
    from compression.lz77 import LZ77Compressor
    from compression.deflate import DeflateCompressor
    from compression.lzw import LZWCompressor
    from compression.bwt import BWTCompressor


class AdaptiveCompressor:
    """Orchestrates adaptive strategy selection, compression, and verification."""

    SUPPORTED_ALGORITHMS = [
        "DEFLATE",
        "LZ77",
        "LZW",
        "HUFFMAN",
        "HYBRID",
        "RLE",
        "BWT",
    ]

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
        strat = strategy.upper()

        if strat == "RLE":
            payload = RLECompressor.compress(data)
            meta = Metadata(file_name=file_name)
            return payload, meta

        elif strat == "HUFFMAN":
            payload, freqs, pad = HuffmanCompressor.compress(data)
            str_freqs = {str(k): v for k, v in freqs.items()}
            meta = Metadata(
                file_name=file_name,
                padding_bits=pad,
                frequencies=str_freqs,
            )
            return payload, meta

        elif strat == "HYBRID":
            payload, freqs, pad, inter_size = HybridCompressor.compress(data)
            str_freqs = {str(k): v for k, v in freqs.items()}
            meta = Metadata(
                file_name=file_name,
                padding_bits=pad,
                intermediate_size=inter_size,
                frequencies=str_freqs,
            )
            return payload, meta

        elif strat == "LZ77":
            payload = LZ77Compressor.compress(data)
            meta = Metadata(file_name=file_name)
            return payload, meta

        elif strat == "DEFLATE":
            payload = DeflateCompressor.compress(data, level=9)
            meta = Metadata(
                file_name=file_name,
                extra_attributes={"engine": DeflateCompressor.ENGINE},
            )
            return payload, meta

        elif strat == "LZW":
            payload = LZWCompressor.compress(data)
            meta = Metadata(file_name=file_name)
            return payload, meta

        elif strat == "BWT":
            payload = BWTCompressor.compress(data)
            meta = Metadata(file_name=file_name)
            return payload, meta

        else:
            # Fallback / Raw Bypass: store uncompressed payload
            meta = Metadata(file_name=file_name)
            return data, meta

    def _decompress_payload(
        self, strategy: str, payload: bytes, meta: Metadata, original_size: int
    ) -> bytes:
        """Decompress payload for a specific strategy."""
        strat = strategy.upper()

        if strat == "RLE":
            return RLECompressor.decompress(payload)

        elif strat == "HUFFMAN":
            int_freqs = meta.get_int_frequencies()
            return HuffmanCompressor.decompress(
                payload, int_freqs, meta.padding_bits, original_size=original_size
            )

        elif strat == "HYBRID":
            int_freqs = meta.get_int_frequencies()
            return HybridCompressor.decompress(
                payload, int_freqs, meta.padding_bits, intermediate_size=meta.intermediate_size
            )

        elif strat == "LZ77":
            return LZ77Compressor.decompress(payload)

        elif strat == "DEFLATE":
            return DeflateCompressor.decompress(payload)

        elif strat == "LZW":
            return LZWCompressor.decompress(payload)

        elif strat == "BWT":
            return BWTCompressor.decompress(payload)

        elif strat in ("NONE", "RAW"):
            return payload

        else:
            raise ValueError(f"Unknown compression algorithm: {strategy}")

    def compress_adaptive(
        self,
        data: bytes,
        file_name: str = "",
        objective: str = "balanced",
        candidates: Optional[List[str]] = None,
        selection_mode: Optional[str] = None,
    ) -> Tuple[bytes, str, PredictionResult, Dict[str, Any]]:
        """Compress data adaptively, evaluating candidates against the specified objective.

        Args:
            data: Input raw bytes.
            file_name: Source file name.
            objective: 'max_compression', 'balanced', or 'fast'.
            candidates: Optional custom list of candidate algorithms to evaluate.
            selection_mode: Backward-compatible mode: 'prediction' or 'evaluate_all'.

        Returns:
            Tuple of:
            - container_bytes: Packaged .ahdc archive bytes
            - selected_strategy: Algorithm chosen
            - prediction: PredictionResult object
            - execution_details: Complete metrics and comparison matrix
        """
        start_time = time.perf_counter()
        t_analysis_start = time.perf_counter()
        profile, prediction = self.analyze(data)
        analysis_duration = time.perf_counter() - t_analysis_start

        orig_size = len(data)

        # Candidate algorithm list
        if candidates:
            candidate_list = candidates
        elif selection_mode == "prediction":
            # In prediction mode, prioritize the predicted candidate and fallbacks
            rec = prediction.recommended_strategy
            candidate_list = [rec] if rec != "NONE" else ["DEFLATE", "HUFFMAN"]
        else:
            candidate_list = self.SUPPORTED_ALGORITHMS

        measured_candidates: Dict[str, Dict[str, Any]] = {}
        comparison_matrix: List[Dict[str, Any]] = []

        # Evaluate candidate algorithms
        for strat in candidate_list:
            try:
                tracemalloc.start()
                t0 = time.perf_counter()
                payload, meta = self._compress_with_strategy(strat, data, file_name)
                t_enc = time.perf_counter() - t0
                _, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                # Build temporary container to measure exact overhead
                temp_container = Container.pack(strat, payload, data, meta)
                final_stored_size = len(temp_container)
                payload_size = len(payload)
                overhead_size = final_stored_size - payload_size

                # Measure decompression time and verify
                t0_dec = time.perf_counter()
                decomp_test = self._decompress_payload(strat, payload, meta, orig_size)
                t_dec = time.perf_counter() - t0_dec
                integrity_ok = (decomp_test == data)

                ratio = round(orig_size / max(final_stored_size, 1), 3)
                space_saved = round(((orig_size - final_stored_size) / max(orig_size, 1)) * 100, 2)
                throughput = round(orig_size / max(t_enc, 1e-9), 1)

                candidate_record = {
                    "payload": payload,
                    "meta": meta,
                    "container_bytes": temp_container,
                    "payload_size": payload_size,
                    "overhead_size": overhead_size,
                    "final_stored_size": final_stored_size,
                    "compression_ratio": ratio,
                    "space_saving_pct": space_saved,
                    "encoding_time": t_enc,
                    "decoding_time": t_dec,
                    "throughput_bps": throughput,
                    "peak_memory_kb": round(peak_mem / 1024, 2),
                    "integrity_passed": integrity_ok,
                }
                measured_candidates[strat] = candidate_record

            except Exception as e:
                # Algorithm failed on this input
                try:
                    tracemalloc.stop()
                except Exception:
                    pass
                measured_candidates[strat] = {
                    "payload": b"",
                    "meta": Metadata(file_name=file_name),
                    "container_bytes": b"",
                    "payload_size": 0,
                    "overhead_size": 0,
                    "final_stored_size": float("inf"),
                    "compression_ratio": 0.0,
                    "space_saving_pct": -100.0,
                    "encoding_time": 0.0,
                    "decoding_time": 0.0,
                    "throughput_bps": 0.0,
                    "peak_memory_kb": 0.0,
                    "integrity_passed": False,
                    "error": str(e),
                }

        # Select the best strategy according to the objective
        selected_strategy, rationale = self.predictor.select_best(
            measured_candidates, objective=objective, original_size=orig_size
        )

        # Prepare final container and package
        if selected_strategy in ("NONE", "RAW"):
            selected_strategy = "NONE"
            final_payload = data
            final_meta = Metadata(file_name=file_name)
            container_bytes = Container.pack("NONE", final_payload, data, final_meta)
            final_stored_size = len(container_bytes)
            final_enc_time = 0.0001
            final_dec_time = 0.0001
            final_peak_mem = 0.0
        else:
            win = measured_candidates[selected_strategy]
            container_bytes = win["container_bytes"]
            final_payload = win["payload"]
            final_meta = win["meta"]
            final_stored_size = win["final_stored_size"]
            final_enc_time = win["encoding_time"]
            final_dec_time = win["decoding_time"]
            final_peak_mem = win["peak_memory_kb"]

        # Build comprehensive Comparison Matrix table
        for strat in candidate_list:
            cand = measured_candidates[strat]
            is_selected = (strat == selected_strategy)
            failed = cand.get("error") is not None

            status_str = "Evaluated" if not failed else "Failed"
            selection_str = "Selected" if is_selected else ("Not Selected" if not failed else "Failed")

            comparison_matrix.append({
                "Algorithm": strat,
                "Evaluation Status": status_str,
                "Original Size (B)": orig_size,
                "Payload Size (B)": cand["payload_size"],
                "Metadata & Header Size (B)": cand["overhead_size"],
                "Final Stored Size (B)": cand["final_stored_size"] if not failed else orig_size,
                "Compression Ratio": cand["compression_ratio"],
                "Space Saved (%)": cand["space_saving_pct"],
                "Compression Time (s)": round(cand["encoding_time"], 5),
                "Decompression Time (s)": round(cand["decoding_time"], 5),
                "Throughput (B/s)": cand["throughput_bps"],
                "Peak Memory (KB)": cand["peak_memory_kb"],
                "Integrity": "PASS" if cand["integrity_passed"] else "FAIL",
                "Selection Result": selection_str,
            })

        # Add Raw Bypass to comparison table if selected or for completeness
        raw_container = Container.pack("NONE", data, data, Metadata(file_name=file_name))
        raw_size = len(raw_container)
        comparison_matrix.append({
            "Algorithm": "Raw Bypass",
            "Evaluation Status": "Evaluated",
            "Original Size (B)": orig_size,
            "Payload Size (B)": orig_size,
            "Metadata & Header Size (B)": raw_size - orig_size,
            "Final Stored Size (B)": raw_size,
            "Compression Ratio": round(orig_size / max(raw_size, 1), 3),
            "Space Saved (%)": round(((orig_size - raw_size) / max(orig_size, 1)) * 100, 2),
            "Compression Time (s)": 0.00001,
            "Decompression Time (s)": 0.00001,
            "Throughput (B/s)": round(orig_size / 0.00001, 1),
            "Peak Memory (KB)": 0.0,
            "Integrity": "PASS",
            "Selection Result": "Selected" if selected_strategy == "NONE" else "Not Selected",
        })

        total_time = time.perf_counter() - start_time

        details = {
            "selected_strategy": selected_strategy,
            "predicted_strategy": prediction.recommended_strategy,
            "selection_objective": objective,
            "selection_rationale": rationale,
            "original_size": orig_size,
            "payload_size": len(final_payload),
            "container_size": len(container_bytes),
            "compression_ratio": round(orig_size / max(len(container_bytes), 1), 3),
            "space_saving_pct": round(((orig_size - len(container_bytes)) / max(orig_size, 1)) * 100, 2),
            "encoding_time": round(final_enc_time, 5),
            "decoding_time": round(final_dec_time, 5),
            "content_analysis_time": round(analysis_duration, 5),
            "total_elapsed_time": round(total_time, 5),
            "throughput_bps": round(orig_size / max(final_enc_time, 1e-9), 1),
            "peak_memory_kb": final_peak_mem,
            "profile": profile,
            "comparison_matrix": comparison_matrix,
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
            - integrity_passed: Boolean indicating exact hash and length match
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

        elif strategy == "LZ77":
            decompressed = LZ77Compressor.decompress(payload)

        elif strategy == "DEFLATE":
            decompressed = DeflateCompressor.decompress(payload)

        elif strategy == "LZW":
            decompressed = LZWCompressor.decompress(payload)

        elif strategy == "BWT":
            decompressed = BWTCompressor.decompress(payload)

        elif strategy in ("NONE", "RAW"):
            decompressed = payload

        else:
            raise ValueError(f"Unknown compression algorithm in archive: {strategy}")

        dec_time = time.perf_counter() - start_time

        # Verify integrity
        computed_sha256 = hashlib.sha256(decompressed).hexdigest()
        hash_match = computed_sha256.lower() == pkg.original_sha256.lower()
        len_match = len(decompressed) == pkg.original_size
        integrity_passed = hash_match and len_match

        status_msg = (
            f"Integrity Check: PASSED (SHA-256 match, {len(decompressed):,} bytes restored exactly)"
            if integrity_passed
            else f"Integrity Check: FAILED (Hash mismatch! Expected {pkg.original_sha256[:12]}..., got {computed_sha256[:12]}...)"
        )

        info = {
            "algorithm": strategy,
            "original_size": pkg.original_size,
            "decompressed_size": len(decompressed),
            "decoding_time": round(dec_time, 5),
            "expected_sha256": pkg.original_sha256,
            "computed_sha256": computed_sha256,
            "file_name": meta.file_name,
            "integrity_passed": integrity_passed,
        }

        return decompressed, integrity_passed, status_msg, info
