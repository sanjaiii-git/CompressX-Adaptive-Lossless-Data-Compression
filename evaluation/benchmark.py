"""Benchmarking framework for comparing RLE, Huffman, Hybrid, Adaptive, and GZIP baseline."""

import gzip
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

        # 1. RLE
        t0 = time.perf_counter()
        rle_comp = RLECompressor.compress(data)
        t_rle_enc = time.perf_counter() - t0

        t0 = time.perf_counter()
        rle_decomp = RLECompressor.decompress(rle_comp)
        t_rle_dec = time.perf_counter() - t0
        rle_valid, _, _ = verify_integrity(data, rle_decomp)

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "RLE",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": len(rle_comp),
            "Ratio": round(orig_size / max(len(rle_comp), 1), 3),
            "Space Saved (%)": round(((orig_size - len(rle_comp)) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_rle_enc, 5),
            "Decoding Time (s)": round(t_rle_dec, 5),
            "Integrity": "PASSED" if rle_valid else "FAILED",
        })

        # 2. Huffman
        t0 = time.perf_counter()
        huff_comp, huff_freq, huff_pad = HuffmanCompressor.compress(data)
        t_huff_enc = time.perf_counter() - t0

        t0 = time.perf_counter()
        huff_decomp = HuffmanCompressor.decompress(
            huff_comp, huff_freq, huff_pad, original_size=orig_size
        )
        t_huff_dec = time.perf_counter() - t0
        huff_valid, _, _ = verify_integrity(data, huff_decomp)

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "Huffman",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": len(huff_comp),
            "Ratio": round(orig_size / max(len(huff_comp), 1), 3),
            "Space Saved (%)": round(((orig_size - len(huff_comp)) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_huff_enc, 5),
            "Decoding Time (s)": round(t_huff_dec, 5),
            "Integrity": "PASSED" if huff_valid else "FAILED",
        })

        # 3. Hybrid (RLE + Huffman)
        t0 = time.perf_counter()
        hyb_comp, hyb_freq, hyb_pad, inter_sz = HybridCompressor.compress(data)
        t_hyb_enc = time.perf_counter() - t0

        t0 = time.perf_counter()
        hyb_decomp = HybridCompressor.decompress(
            hyb_comp, hyb_freq, hyb_pad, intermediate_size=inter_sz
        )
        t_hyb_dec = time.perf_counter() - t0
        hyb_valid, _, _ = verify_integrity(data, hyb_decomp)

        results.append({
            "Dataset": dataset_name,
            "Algorithm": "Hybrid (RLE+Huffman)",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": len(hyb_comp),
            "Ratio": round(orig_size / max(len(hyb_comp), 1), 3),
            "Space Saved (%)": round(((orig_size - len(hyb_comp)) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_hyb_enc, 5),
            "Decoding Time (s)": round(t_hyb_dec, 5),
            "Integrity": "PASSED" if hyb_valid else "FAILED",
        })

        # 4. Adaptive System (with full Container package)
        t0 = time.perf_counter()
        adapt_pkg, adapt_strat, pred_res, details = self.adaptive_comp.compress_adaptive(
            data, file_name=dataset_name, selection_mode="evaluate_all"
        )
        t_adapt_enc = time.perf_counter() - t0

        t0 = time.perf_counter()
        adapt_decomp, adapt_valid, _, _ = AdaptiveCompressor.decompress_container(adapt_pkg)
        t_adapt_dec = time.perf_counter() - t0

        results.append({
            "Dataset": dataset_name,
            "Algorithm": f"Adaptive ({adapt_strat})",
            "Original Size (B)": orig_size,
            "Compressed Size (B)": len(adapt_pkg),
            "Ratio": round(orig_size / max(len(adapt_pkg), 1), 3),
            "Space Saved (%)": round(((orig_size - len(adapt_pkg)) / max(orig_size, 1)) * 100, 2),
            "Encoding Time (s)": round(t_adapt_enc, 5),
            "Decoding Time (s)": round(t_adapt_dec, 5),
            "Integrity": "PASSED" if adapt_valid else "FAILED",
        })

        # 5. GZIP (Industrial standard baseline)
        t0 = time.perf_counter()
        gzip_comp = gzip.compress(data)
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
            "Integrity": "PASSED" if gzip_valid else "FAILED",
        })

        analysis_summary = {
            "dataset": dataset_name,
            "profile": profile,
            "prediction": prediction,
            "actual_selected": adapt_strat,
            "prediction_match": details["prediction_accurate"],
        }

        return results, analysis_summary

    def run_all(self, dataset_dict: Dict[str, str]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Run benchmark across all dataset files in dictionary."""
        all_rows = []
        all_summaries = []

        for name, path in dataset_dict.items():
            if not os.path.exists(path):
                continue
            with open(path, "rb") as f:
                data = f.read()
            rows, summary = self.run_single_dataset(name, data)
            all_rows.extend(rows)
            all_summaries.append(summary)

        df = pd.DataFrame(all_rows)
        return df, all_summaries


if __name__ == "__main__":
    from datasets.generate_datasets import DATASET_DIR, generate_all_datasets

    dataset_files = {
        "Dataset A (Repetitive)": os.path.join(DATASET_DIR, "dataset_a_repetitive.txt"),
        "Dataset B (Skewed)": os.path.join(DATASET_DIR, "dataset_b_skewed.txt"),
        "Dataset C (Natural Text)": os.path.join(DATASET_DIR, "dataset_c_natural_text.txt"),
        "Dataset D (Server Logs)": os.path.join(DATASET_DIR, "dataset_d_server_logs.log"),
        "Dataset E (Random Data)": os.path.join(DATASET_DIR, "dataset_e_random_data.bin"),
    }

    runner = BenchmarkRunner()
    df, summaries = runner.run_all(dataset_files)

    print("\n================ BENCHMARK RESULTS ================")
    print(df.to_string(index=False))

    print("\n================ PREDICTION EVALUATION ================")
    correct = 0
    total = len(summaries)
    for s in summaries:
        pred = s["prediction"]
        act = s["actual_selected"]
        match = "[OK] CORRECT" if s["prediction_match"] else "[!] MISMATCH"
        if s["prediction_match"]:
            correct += 1
        print(f"[{s['dataset']}]")
        print(f"  Entropy: {s['profile']['entropy']} bits/sym | Repetition: {s['profile']['repetition_percentage']}%")
        print(f"  Predicted: {pred.recommended_strategy} | Actual Selected: {act} -> {match}")
        print(f"  Rationale: {pred.explanation[:120]}...\n")

    accuracy = (correct / total) * 100.0 if total > 0 else 0.0
    print(f"Overall Prediction Accuracy: {accuracy:.1f}% ({correct}/{total})")
