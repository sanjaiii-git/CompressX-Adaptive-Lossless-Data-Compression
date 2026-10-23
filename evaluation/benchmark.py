"""Benchmarking framework for comparing RLE, Huffman, Hybrid, LZ77, DEFLATE, LZW, BWT, Adaptive, and GZIP."""

import gzip
import json
import os
import sys
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compression.adaptive import AdaptiveCompressor
from compression.huffman import HuffmanCompressor
from compression.hybrid import HybridCompressor
from compression.rle import RLECompressor
from compression.lz77 import LZ77Compressor
from compression.deflate import DeflateCompressor
from compression.lzw import LZWCompressor
from compression.bwt import BWTCompressor
from evaluation.metrics import verify_integrity


class BenchmarkRunner:
    """Automated benchmark runner across heterogeneous datasets."""

    def __init__(self):
        self.adaptive_comp = AdaptiveCompressor()

    def run_single_dataset(
        self, dataset_name: str, data: bytes
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run all algorithms on a single dataset and calculate comparative metrics."""
        orig_size = len(data)

        # Pre-compression analysis and prediction
        profile, prediction = self.adaptive_comp.analyze(data)

        results = []

        def benchmark_method(name: str, compress_fn, decompress_fn):
            tracemalloc.start()
            t0 = time.perf_counter()
            comp_data = compress_fn(data)
            t_enc = time.perf_counter() - t0
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            t0 = time.perf_counter()
            decomp_data = decompress_fn(comp_data)
            t_dec = time.perf_counter() - t0

            is_valid, _, _ = verify_integrity(data, decomp_data)
            comp_size = len(comp_data)
            ratio = round(orig_size / max(comp_size, 1), 3)
            saving = round(((orig_size - comp_size) / max(orig_size, 1)) * 100, 2)
            throughput = round(orig_size / max(t_enc, 1e-9), 1)

            results.append({
                "Dataset": dataset_name,
                "Algorithm": name,
                "Original Size (B)": orig_size,
                "Compressed Size (B)": comp_size,
                "Ratio": ratio,
                "Space Saved (%)": saving,
                "Encoding Time (s)": round(t_enc, 5),
                "Decoding Time (s)": round(t_dec, 5),
                "Throughput (B/s)": throughput,
                "Peak Memory (KB)": round(peak_mem / 1024, 2),
                "Integrity": "PASSED" if is_valid else "FAILED",
            })

        # 1. RLE
        benchmark_method("RLE", RLECompressor.compress, RLECompressor.decompress)

        # 2. Huffman
        def huff_comp(d):
            c, freqs, pad = HuffmanCompressor.compress(d)
            return (c, freqs, pad)

        def huff_decomp(pkg):
            c, freqs, pad = pkg
            return HuffmanCompressor.decompress(c, freqs, pad, original_size=orig_size)

        tracemalloc.start()
        t0 = time.perf_counter()
        h_pkg = huff_comp(data)
        t_huff_enc = time.perf_counter() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        t0 = time.perf_counter()
        h_decomp = huff_decomp(h_pkg)
        t_huff_dec = time.perf_counter() - t0
        h_valid, _, _ = verify_integrity(data, h_decomp)
        h_size = len(h_pkg[0])

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "Huffman",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": h_size,
            "Ratio": round(orig_size / max(h_size, 1), 3),
            "Space Saved (%)": round(((orig_size - h_size) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_huff_enc, 5),
            "Decoding Time (s)": round(t_huff_dec, 5),
            "Throughput (B/s)": round(orig_size / max(t_huff_enc, 1e-9), 1),
            "Peak Memory (KB)": round(peak_mem / 1024, 2),
            "Integrity": "PASSED" if h_valid else "FAILED",
        })

        # 3. Hybrid (RLE + Huffman)
        def hyb_comp(d):
            c, freqs, pad, inter = HybridCompressor.compress(d)
            return (c, freqs, pad, inter)

        def hyb_decomp(pkg):
            c, freqs, pad, inter = pkg
            return HybridCompressor.decompress(c, freqs, pad, intermediate_size=inter)

        tracemalloc.start()
        t0 = time.perf_counter()
        hyb_pkg = hyb_comp(data)
        t_hyb_enc = time.perf_counter() - t0
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        t0 = time.perf_counter()
        hyb_d = hyb_decomp(hyb_pkg)
        t_hyb_dec = time.perf_counter() - t0
        hyb_valid, _, _ = verify_integrity(data, hyb_d)
        hyb_size = len(hyb_pkg[0])

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "Hybrid (RLE+Huffman)",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": hyb_size,
            "Ratio": round(orig_size / max(hyb_size, 1), 3),
            "Space Saved (%)": round(((orig_size - hyb_size) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_hyb_enc, 5),
            "Decoding Time (s)": round(t_hyb_dec, 5),
            "Throughput (B/s)": round(orig_size / max(t_hyb_enc, 1e-9), 1),
            "Peak Memory (KB)": round(peak_mem / 1024, 2),
            "Integrity": "PASSED" if hyb_valid else "FAILED",
        })

        # 4. LZ77
        benchmark_method("LZ77", LZ77Compressor.compress, LZ77Compressor.decompress)

        # 5. DEFLATE (Standard Library RFC 1951)
        benchmark_method("DEFLATE", DeflateCompressor.compress, DeflateCompressor.decompress)

        # 6. LZW
        benchmark_method("LZW", LZWCompressor.compress, LZWCompressor.decompress)

        # 7. BWT
        benchmark_method("BWT", BWTCompressor.compress, BWTCompressor.decompress)

        # 8. CompressX Adaptive (Full Container Pipeline)
        c_bytes, chosen_strat, pred_obj, details = self.adaptive_comp.compress_adaptive(
            data, file_name=dataset_name, objective="balanced"
        )
        decomp_bytes, ad_valid, _, info = AdaptiveCompressor.decompress_container(c_bytes)
        ad_size = len(c_bytes)

        results.append({
            "Dataset": dataset_name,
            "Algorithm": f"CompressX Adaptive ({chosen_strat})",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": ad_size,
            "Ratio": details["compression_ratio"],
            "Space Saved (%)": details["space_saving_pct"],
            "Encoding Time (s)": details["encoding_time"],
            "Decoding Time (s)": info["decoding_time"],
            "Throughput (B/s)": details["throughput_bps"],
            "Peak Memory (KB)": details["peak_memory_kb"],
            "Integrity": "PASSED" if ad_valid else "FAILED",
        })

        # 9. GZIP Baseline
        t0 = time.perf_counter()
        gzip_comp = gzip.compress(data, compresslevel=9)
        t_gzip_enc = time.perf_counter() - t0

        t0 = time.perf_counter()
        gzip_decomp = gzip.decompress(gzip_comp)
        t_gzip_dec = time.perf_counter() - t0
        gzip_valid, _, _ = verify_integrity(data, gzip_decomp)

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "GZIP (Baseline)",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": len(gzip_comp),
            "Ratio": round(orig_size / max(len(gzip_comp), 1), 3),
            "Space Saved (%)": round(((orig_size - len(gzip_comp)) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_gzip_enc, 5),
            "Decoding Time (s)": round(t_gzip_dec, 5),
            "Throughput (B/s)": round(orig_size / max(t_gzip_enc, 1e-9), 1),
            "Peak Memory (KB)": 0.0,
            "Integrity": "PASSED" if gzip_valid else "FAILED",
        })

        summary = {
            "dataset": dataset_name,
            "original_size": orig_size,
            "profile": profile,
            "prediction": prediction,
            "actual_selected": chosen_strat,
            "prediction_match": (
                chosen_strat == prediction.recommended_strategy
                or (chosen_strat in ("RLE", "HYBRID") and prediction.recommended_strategy in ("RLE", "HYBRID"))
                or (chosen_strat in ("DEFLATE", "LZ77", "LZW") and prediction.recommended_strategy in ("DEFLATE", "LZ77", "LZW"))
            ),
        }

        return results, summary

    def run_all(
        self, dataset_files: Dict[str, str], output_dir: Optional[str] = None
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Run benchmark on all datasets and save machine-readable results."""
        all_results = []
        all_summaries = []

        for name, path in dataset_files.items():
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = f.read()
                results, summary = self.run_single_dataset(name, data)
                all_results.extend(results)
                all_summaries.append(summary)

        df = pd.DataFrame(all_results)

        # Save to disk if requested
        target_dir = output_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "results"
        )
        os.makedirs(target_dir, exist_ok=True)

        csv_path = os.path.join(target_dir, "benchmark_results.csv")
        json_path = os.path.join(target_dir, "benchmark_results.json")

        df.to_csv(csv_path, index=False)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        return df, all_summaries
