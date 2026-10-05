# CompressX (v2.0) — Adaptive Data Compression & Analysis
**Advanced Lossless Data Compression Tool & Research Platform**

[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Version: 2.0](https://img.shields.io/badge/version-2.0.0-indigo.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 37 Passed](https://img.shields.io/badge/tests-37%20passed-brightgreen.svg)]()
[![Integrity: Lossless SHA-256](https://img.shields.io/badge/integrity-SHA--256%20verified-success.svg)]()
[![PDF Reports: ReportLab](https://img.shields.io/badge/reports-PDF%20Export-red.svg)]()

---

## 📌 Executive Summary
**CompressX (v2.0)** is a production-grade, advanced lossless data compression software platform featuring an **Intelligent Decision Engine**. Instead of blindly applying a single compression algorithm, CompressX profiles the statistical and information-theoretic structure of any incoming data stream in-memory prior to compression—measuring **Shannon Entropy $H(X)$**, **Average Run Length $\bar{R}$**, **Repetition Percentage**, and **Frequency Gini Skewness**.

Based on empirical characteristics and a multi-criteria cost model balancing space savings, latency, and memory footprint, CompressX automatically orchestrates:
1. **Run-Length Encoding (RLE):** Collapses consecutive repeating symbols into compact (count, byte) tokens.
2. **Huffman Coding:** Constructs optimal prefix-free trees based on non-uniform character probability distributions.
3. **Sequential Hybrid (RLE + Huffman):** Pre-processes runs via RLE, then shrinks the resulting token distribution using Huffman.
4. **Raw Storage Bypass:** Prevents archive expansion on high-entropy incompressible data ($H(X) \approx 8.0$ bits/symbol).

### ✨ New in Version 2.0
- **📄 Downloadable PDF Technical Reports:** Publication-quality technical reports with embedded vector/raster comparison charts, mathematical metadata, and audit footers.
- **💾 Custom Archive Container (.ahdc):** Binary archive format with 47-byte fixed headers and embedded cryptographic SHA-256 validation.
- **📊 Exportable Telemetry:** JSON analysis data export for data engineering pipelines.
- **📜 Persistent Job History:** Local JSON tracking of all compression operations.
- **🎨 Modern SaaS Dashboard UI:** Redesigned responsive interface with progress indicators, cards, and before/after comparisons.
- **🔒 100% Lossless Verification:** Automated SHA-256 hash match checks on every decompression.

---

## 🏛️ System Architecture

```
                       INPUT FILE (.txt, .csv, .log, .bin)
                                      │
                                      ▼
                      [ In-Memory Data Profiler ]
                      ├── Shannon Entropy H(X)
                      ├── Repetition Rate & Run Lengths
                      └── Gini Skew & Alphabet Size
                                      │
                                      ▼
                      [ Intelligent Decision Engine ]
                      ├── Multi-Criteria Cost Function
                      └── Heuristic Rule Classifier
                                      │
             ┌────────────────────────┼────────────────────────┐
             ▼                        ▼                        ▼
      [ RLE Engine ]          [ Huffman Engine ]       [ Hybrid Pipeline ]
     Continuous runs         Priority Min-Heap Tree     Stage 1: RLE
     Byte-pair tokens        Deterministic Prefix Code  Stage 2: Huffman
             └────────────────────────┬────────────────────────┘
                                      │
                                      ▼
                     [ Custom Container Packaging (.ahdc) ]
                     ├── Header (47B): Magic 'AHDC', SHA-256
                     ├── Metadata (JSON): Frequency Map, Padding
                     └── Payload: Compressed Bitstream
                                      │
                                      ▼
                  Lossless Decompression & Integrity Check
                  (Original SHA-256 == Decompressed SHA-256)
```

---

## 🔬 Mathematical Foundations

- **Shannon's Source Coding Theorem:**
  $$H(X) = - \sum_{i=1}^{N} p_i \log_2(p_i) \quad \implies \quad \bar{L} \ge H(X)$$
- **RLE Profitability Boundary:**
  $$\text{Compressed Size} = 2 \cdot M < N \iff \bar{R} = \frac{N}{M} > 2.0$$
- **Prefix Coding (Kraft-McMillan Inequality):**
  $$\sum_{i=1}^{N} 2^{-\ell_i} \le 1$$
- **Multi-Objective Cost Model:**
  $$\text{Cost} = w_{\text{size}} \cdot S_{\text{norm}} + w_{\text{time}} \cdot T_{\text{norm}} + w_{\text{mem}} \cdot M_{\text{norm}}$$

---

## 📂 Project Directory Structure

```text
adaptive-compression/
├── app/
│   └── app.py                     # Interactive Streamlit Web Application
├── compression/
│   ├── __init__.py
│   ├── rle.py                     # Run-Length Encoding compressor & decompressor
│   ├── huffman.py                 # Huffman min-heap tree & bit-packing engine
│   ├── hybrid.py                  # Sequential Two-Stage RLE + Huffman pipeline
│   └── adaptive.py                # Adaptive decision orchestrator & container builder
├── analysis/
│   ├── __init__.py
│   ├── entropy.py                 # Shannon entropy calculator & theoretical bounds
│   ├── repetition.py              # Run-length analyzer & mathematical threshold checks
│   ├── statistics.py              # Symbol profiling & Gini skewness calculator
│   └── predictor.py               # Rule-based & cost-driven strategy predictor
├── storage/
│   ├── __init__.py
│   ├── container.py               # Binary archive container (.ahdc) pack & unpack
│   └── metadata.py                # JSON metadata serialization & frequency tables
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                 # Benchmarking timers, memory tracking & verification
│   ├── benchmark.py               # Automated benchmark across datasets A through E
│   ├── report_generator.py        # PDF technical report generator (ReportLab)
│   ├── visualization.py           # Matplotlib chart generator (PNG assets)
│   └── charts/                    # Generated analytical charts
├── storage/
│   ├── __init__.py
│   ├── container.py               # Binary archive container (.ahdc) pack & unpack
│   ├── metadata.py                # JSON metadata serialization & frequency tables
│   └── history.py                 # Persistent JSON compression job history tracker
├── datasets/
│   ├── generate_datasets.py       # Generator for standardized datasets A-E
│   ├── dataset_a_repetitive.txt   # Highly repetitive data
│   ├── dataset_b_skewed.txt       # Zipfian skewed letter frequencies
│   ├── dataset_c_natural_text.txt # Natural English text
│   ├── dataset_d_server_logs.log  # Web server telemetry logs
│   └── dataset_e_random_data.bin  # High-entropy random data (incompressible)
├── tests/
│   ├── test_rle.py                # Unit tests for RLE
│   ├── test_huffman.py            # Unit tests for Huffman
│   ├── test_hybrid.py             # Unit tests for Hybrid pipeline
│   ├── test_adaptive.py           # Unit tests for prediction & adaptive engine
│   ├── test_container.py          # Unit tests for .ahdc container format
│   ├── test_report_and_history.py # Unit tests for PDF reports & history tracking
│   └── test_integrity.py          # Lossless integrity roundtrip on all edge cases
├── docs/
│   ├── PROJECT_REPORT.md          # Comprehensive academic project report
│   ├── PRESENTATION_SLIDES.md     # Viva presentation slide-by-slide script
│   └── VIVA_QUESTIONS.md          # 25+ Viva voce questions and model answers
├── requirements.txt               # Dependencies
└── README.md                      # Project documentation
```

---

## ⚡ Installation & Quickstart

### 1. Prerequisites
- Python 3.10 or higher.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Unit Tests (37 Tests)
```bash
python -m pytest tests/ -v
```

### 4. Execute Benchmark Suite
```bash
python -m evaluation.benchmark
```

### 5. Launch Interactive Streamlit UI
```bash
streamlit run app/app.py
```

---

## 📊 Experimental Results Summary (50 KB Datasets)

| Dataset | Characteristic | Best Algorithm | Ratio | Space Saved | Prediction | Integrity |
|---|---|---|---|---|---|---|
| **Dataset A** | Repetitive (\(\bar{R} = 133.7\)) | **Hybrid (RLE+Huffman)** | **85.19x** | **98.83%** | CORRECT | PASSED |
| **Dataset B** | Skewed Frequencies | **Huffman** | **1.79x** | **43.97%** | CORRECT | PASSED |
| **Dataset C** | Natural Text | **Huffman** | **1.85x** | **45.87%** | CORRECT | PASSED |
| **Dataset D** | Server Logs | **Huffman** | **1.59x** | **36.92%** | CORRECT | PASSED |
| **Dataset E** | High-Entropy Noise | **NONE (Raw Bypass)** | **0.996x** | **-0.38%** | CORRECT | PASSED |

**Overall Prediction Accuracy:** **100.0% (5/5)**  
**Lossless Verification Rate:** **100.0% (PASSED on all tests)**

---

## 🎓 Academic Viva & Presentation Resources
- **Full Project Report:** [`docs/PROJECT_REPORT.md`](file:///d:/project/adaptive_data_compression/docs/PROJECT_REPORT.md)
- **Presentation Deck Script:** [`docs/PRESENTATION_SLIDES.md`](file:///d:/project/adaptive_data_compression/docs/PRESENTATION_SLIDES.md)
- **Viva Voce Q&A Preparation:** [`docs/VIVA_QUESTIONS.md`](file:///d:/project/adaptive_data_compression/docs/VIVA_QUESTIONS.md)
