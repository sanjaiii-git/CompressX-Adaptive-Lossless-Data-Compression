"""Visualization generator for benchmark analysis, charts, and report assets."""

import os
import sys
from typing import List, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend suitable for headless scripts
import matplotlib.pyplot as plt
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.benchmark import BenchmarkRunner
from datasets.generate_datasets import DATASET_DIR


def generate_benchmark_charts(output_dir: str) -> List[str]:
    """Execute benchmark and generate analytical charts."""
    os.makedirs(output_dir, exist_ok=True)

    dataset_files = {
        "Dataset A (Repetitive)": os.path.join(DATASET_DIR, "dataset_a_repetitive.txt"),
        "Dataset B (Skewed)": os.path.join(DATASET_DIR, "dataset_b_skewed.txt"),
        "Dataset C (Natural Text)": os.path.join(DATASET_DIR, "dataset_c_natural_text.txt"),
        "Dataset D (Server Logs)": os.path.join(DATASET_DIR, "dataset_d_server_logs.log"),
        "Dataset E (Random Data)": os.path.join(DATASET_DIR, "dataset_e_random_data.bin"),
    }

    runner = BenchmarkRunner()
    df, summaries = runner.run_all(dataset_files)

    generated_plots = []

    # 1. Bar Chart: Compression Ratio by Algorithm across Datasets
    plt.figure(figsize=(12, 6))
    datasets = df["Dataset"].unique()
    algorithms = ["RLE", "Huffman", "Hybrid (RLE+Huffman)", "GZIP (Baseline)"]

    # Pivot table for plotting
    pivot_df = df.pivot(index="Dataset", columns="Algorithm", values="Ratio")
    # Clean up column names if needed
    cols = [c for c in pivot_df.columns if any(a in c for a in ["RLE", "Huffman", "Hybrid", "Adaptive", "GZIP"])]
    pivot_df[cols].plot(kind="bar", figsize=(13, 6), colormap="viridis", edgecolor="black", width=0.8)

    plt.title("Compression Ratio Comparison Across Datasets (Higher is Better)", fontsize=14, fontweight="bold")
    plt.ylabel("Compression Ratio (Original / Compressed)", fontsize=12)
    plt.xlabel("Dataset", fontsize=12)
    plt.xticks(rotation=15, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    ratio_chart_path = os.path.join(output_dir, "compression_ratio_comparison.png")
    plt.savefig(ratio_chart_path, dpi=300)
    plt.close()
    generated_plots.append(ratio_chart_path)

    # 2. Bar Chart: Space Savings (%)
    plt.figure(figsize=(12, 6))
    pivot_space = df.pivot(index="Dataset", columns="Algorithm", values="Space Saved (%)")
    pivot_space.plot(kind="bar", figsize=(13, 6), colormap="plasma", edgecolor="black", width=0.8)

    plt.axhline(0, color="gray", linewidth=1.2, linestyle="--")
    plt.title("Space Savings Percentage Comparison (Higher is Better, Negative = Expansion)", fontsize=14, fontweight="bold")
    plt.ylabel("Space Saved (%)", fontsize=12)
    plt.xlabel("Dataset", fontsize=12)
    plt.xticks(rotation=15, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    space_chart_path = os.path.join(output_dir, "space_savings_comparison.png")
    plt.savefig(space_chart_path, dpi=300)
    plt.close()
    generated_plots.append(space_chart_path)

    # 3. Scatter Plot: Shannon Entropy vs Achieved Compression Ratio (Huffman)
    entropies = [s["profile"]["entropy"] for s in summaries]
    huff_ratios = []
    for s in summaries:
        ds = s["dataset"]
        row = df[(df["Dataset"] == ds) & (df["Algorithm"] == "Huffman")]
        if not row.empty:
            huff_ratios.append(row["Ratio"].values[0])
        else:
            huff_ratios.append(1.0)

    plt.figure(figsize=(8, 5))
    plt.scatter(entropies, huff_ratios, color="#1f77b4", s=120, edgecolors="black", zorder=3)
    for i, txt in enumerate([s["dataset"].split(" ")[1] for s in summaries]):
        plt.annotate(txt, (entropies[i] + 0.1, huff_ratios[i]), fontsize=10)

    plt.title("Shannon Entropy vs. Huffman Compression Ratio", fontsize=13, fontweight="bold")
    plt.xlabel("Shannon Entropy (bits/symbol)", fontsize=11)
    plt.ylabel("Huffman Compression Ratio", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    entropy_chart_path = os.path.join(output_dir, "entropy_vs_compression_ratio.png")
    plt.savefig(entropy_chart_path, dpi=300)
    plt.close()
    generated_plots.append(entropy_chart_path)

    print(f"Generated {len(generated_plots)} evaluation charts in {output_dir}")
    return generated_plots


if __name__ == "__main__":
    generate_benchmark_charts(os.path.join(os.path.dirname(os.path.abspath(__file__)), "charts"))
