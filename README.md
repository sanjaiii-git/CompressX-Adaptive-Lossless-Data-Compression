# CompressX — Intelligent Adaptive Lossless Data Compression System

[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Version: 2.1](https://img.shields.io/badge/version-2.1.0-indigo.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 85 Passed](https://img.shields.io/badge/tests-85%20passed-brightgreen.svg)]()
[![Integrity: Lossless SHA-256](https://img.shields.io/badge/integrity-SHA--256%20verified-success.svg)]()
[![PDF Reports: ReportLab](https://img.shields.io/badge/reports-PDF%20Export-red.svg)]()

---

## 📌 Executive Summary

**CompressX** is an enterprise-grade, intelligent adaptive lossless data compression system. Instead of blindly applying a single compression algorithm, CompressX profiles the statistical, entropy, and repetition characteristics of any incoming binary file in-memory—measuring **Shannon Entropy $H(X)$**, **Average Run Length $\bar{R}$**, **Repetition Percentage**, **Cardinality**, and **Frequency Gini Skewness**.

Based on actual measured empirical performance and configurable optimization objectives (**Balanced**, **Maximum Compression**, or **Fast Compression**), CompressX automatically selects and packages data using the optimal candidate from an 8-algorithm compression engine, validates exact bit-for-bit lossless integrity via cryptographic **SHA-256**, and generates publication-quality **PDF Technical Reports**.

---

## 🚀 Key Features

- **8 Lossless Compression Algorithms**:
  1. **Run-Length Encoding (RLE)**: Linear $O(N)$ run-length tokenization for repetitive data.
  2. **Huffman Coding**: Priority-queue binary prefix tree optimization for skewed symbol distributions.
  3. **Sequential Hybrid (RLE + Huffman)**: Two-stage pipeline combining run-tokenization with entropy reduction.
  4. **LZ77**: 4 KB sliding-window dictionary matching with bit-packed flag bytes.
  5. **DEFLATE (RFC 1951)**: Standard LZ77 + Huffman bitstream compression via Python standard library `zlib`.
  6. **LZW (Lempel–Ziv–Welch)**: Dynamic 16-bit dictionary encoder with KwKwK edge-case handling.
  7. **BWT (Burrows–Wheeler Transform)**: Block-based BWT + Move-To-Front (MTF) + Zero-run RLE stage.
  8. **Raw Storage Bypass (NONE)**: Prevents file expansion on high-entropy incompressible or encrypted data.

- **Intelligent Multi-Objective Decision Engine**:
  - **Balanced** *(Default)*: Multi-criteria optimization balancing storage savings, compression latency, and memory footprint.
  - **Maximum Compression**: Prioritizes the strictly smallest final archive size.
  - **Fast Compression**: Prioritizes execution speed while preventing file expansion.
  - **Automatic Raw Bypass**: Activates when all candidate algorithms expand the file size.

- **Cryptographic SHA-256 Integrity Verification**:
  - Automatically decompresses every created container and performs bit-for-bit SHA-256 validation.
  - Guarantees 100% exact restoration without data loss.

- **Complete 14-Column Algorithm Comparison Matrix**:
  - Live side-by-side performance audit covering: Algorithm, Evaluation Status, Original Size, Compressed Payload, Container Overhead, Final Stored Size, Compression Ratio, Space Saved (%), Compression Time, Decompression Time, Throughput (B/s), Peak Memory (KB), Integrity Status, and Selection Result.

- **Professional 7-Section PDF Technical Report**:
  - Section 1: Executive Summary & File Metadata
  - Section 2: Content Analysis & Empirical Entropy Profile
  - Section 3: Algorithm Comparison Matrix
  - Section 4: Selection Rationale & Objective Justification
  - Section 5: Side-by-Side Visual Performance Charts
  - Section 6: Verification & Exact Restoration Audit
  - Section 7: System Configuration & Container Technical Specification

- **Custom Binary Container (`.ahdc`)**:
  - Standardized binary format with 47-byte fixed header, algorithm ID, SHA-256 checksum, JSON metadata, and compressed payload. Fully backward-compatible.

- **Modern Clean Light UI**:
  - Responsive light-themed dashboard with emerald accents, metric cards, progress bars, and comprehensive analytics.

---

## 🏛️ System Architecture

```text
                       INPUT BINARY FILE (.txt, .csv, .log, .bin, etc.)
                                       │
                                       ▼
                       [ In-Memory Content Profiler ]
                       ├── Shannon Entropy H(X)
                       ├── Average Run Length & Repetition Rate
                       ├── Frequency Gini Skew & Cardinality
                       └── Theoretical Compressibility Bound
                                       │
                                       ▼
                     [ Multi-Objective Candidate Evaluator ]
                     ├── Objectives: Balanced | Max Compression | Fast
                     ├── Benchmark Candidates (time.perf_counter + tracemalloc)
                     └── Measure Exact Container Overhead
                                       │
       ┌───────────┬───────────┬───────┴───┬───────────┬───────────┬───────────┐
       ▼           ▼           ▼           ▼           ▼           ▼           ▼
    [ RLE ]    [ Huffman ]  [ Hybrid ]  [ LZ77 ]   [ DEFLATE ]  [ LZW ]     [ BWT ]
       └───────────┴───────────┴───────┬───┴───────────┴───────────┴───────────┘
                                       │
                                       ▼
                       [ Optimal Candidate Selected ]
                         (Or Raw Bypass if size expands)
                                       │
                                       ▼
                     [ Custom Container Packaging (.ahdc) ]
                     ├── Header (47B): Magic 'AHDC', Alg ID, SHA-256
                     ├── Metadata: File attributes, frequency tables
                     └── Payload: Lossless compressed bitstream
                                       │
                                       ▼
                     [ Lossless Verification & PDF Reporting ]
                     ├── Byte-for-Byte SHA-256 Validation
                     └── Downloadable 7-Section Technical Report
```

---

## 🔬 Mathematical Foundations

- **Shannon's Source Coding Theorem**:
  $$H(X) = - \sum_{i=1}^{N} p_i \log_2(p_i) \quad \implies \quad \bar{L} \ge H(X)$$
- **Theoretical Compression Ratio Upper Bound**:
  $$\text{Ratio}_{\max} = \frac{8.0}{H(X)}$$
- **Compression Ratio**:
  $$\text{Compression Ratio} = \frac{\text{Original Size}}{\text{Final Stored Size}}$$
- **Space Saved Percentage**:
  $$\text{Space Saved (\%)} = \left(\frac{\text{Original Size} - \text{Final Stored Size}}{\text{Original Size}}\right) \times 100$$
- **Compression Throughput**:
  $$\text{Throughput} = \frac{\text{Original Size (Bytes)}}{\text{Compression Time (Seconds)}}$$
- **Multi-Objective Cost Model**:
  $$\text{Cost} = w_{\text{size}} \cdot S_{\text{norm}} + w_{\text{time}} \cdot T_{\text{norm}} + w_{\text{mem}} \cdot M_{\text{norm}}$$

---

## 📂 Project Structure

```text
├── app/
│   └── app.py                     # Clean Streamlit Web Dashboard
├── compression/
│   ├── __init__.py                # Module exports for all 8 algorithms
│   ├── rle.py                     # Run-Length Encoding compressor & decompressor
│   ├── huffman.py                 # Huffman min-heap tree & bit-packing engine
│   ├── hybrid.py                  # Sequential Two-Stage RLE + Huffman pipeline
│   ├── lz77.py                    # LZ77 sliding-window dictionary compressor
│   ├── deflate.py                 # RFC 1951 DEFLATE engine (zlib)
│   ├── lzw.py                     # LZW dictionary compressor with KwKwK handling
│   ├── bwt.py                     # Burrows-Wheeler Transform + MTF + Zero-run RLE
│   └── adaptive.py                # Multi-objective adaptive selector & benchmark orchestrator
├── analysis/
│   ├── __init__.py
│   ├── entropy.py                 # Shannon entropy calculator & theoretical bounds
│   ├── repetition.py              # Run-length analyzer & pattern statistics
│   ├── statistics.py              # Symbol frequency profiler & Gini coefficient
│   └── predictor.py               # Objective-driven decision engine & candidate selector
├── storage/
│   ├── __init__.py
│   ├── container.py               # Binary archive container (.ahdc) pack & unpack
│   ├── metadata.py                # JSON metadata serialization & frequency tables
│   └── history.py                 # Persistent JSON compression job history tracker
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                 # Monotonic timers, memory tracking & verification
│   ├── benchmark.py               # Automated benchmark across all 8 algorithms
│   ├── report_generator.py        # 7-section PDF technical report generator (ReportLab)
│   └── visualization.py           # Matplotlib chart generator
├── datasets/
│   ├── generate_datasets.py       # Generator for standardized test datasets
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
│   ├── test_integrity.py          # Lossless integrity roundtrip on all algorithms
│   └── test_new_algorithms.py     # Tests for LZ77, DEFLATE, LZW, BWT, and objectives
├── docs/
│   ├── PROJECT_REPORT.md          # Comprehensive technical report
│   ├── PRESENTATION_SLIDES.md     # Viva presentation slide-by-slide script
│   └── VIVA_QUESTIONS.md          # Viva voce questions and model answers
├── .streamlit/
│   └── config.toml                # Light theme configuration
├── requirements.txt               # Dependencies
└── README.md                      # Project documentation
```

---

## ⚡ Installation & Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/sanjaiii-git/autocompression_and_decompression.git
cd autocompression_and_decompression
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Unit Tests (85 Tests)
```bash
python -m pytest tests/ -v
```

### 4. Execute Benchmark Suite
```bash
python -m evaluation.benchmark
```

### 5. Launch Interactive Dashboard
```bash
streamlit run app/app.py
```

---

## 📊 Benchmark Comparison Across Datasets

| Dataset | Type | Best Algorithm | Stored Ratio | Space Saved | Verification |
|---|---|---|---|---|---|
| **Dataset A** | Repetitive ($\bar{R} = 133.7$) | **DEFLATE / Hybrid** | **>85.0x** | **>98.5%** | **PASSED** |
| **Dataset B** | Skewed Frequencies | **DEFLATE / Huffman** | **>1.80x** | **>45.0%** | **PASSED** |
| **Dataset C** | Natural Text | **DEFLATE** | **>2.10x** | **>52.0%** | **PASSED** |
| **Dataset D** | Server Logs | **DEFLATE** | **>2.30x** | **>56.0%** | **PASSED** |
| **Dataset E** | High-Entropy Noise | **Raw Bypass (NONE)** | **1.00x** | **0.0%** | **PASSED** |

- **Lossless Verification Rate**: **100% (Bit-for-bit SHA-256 match on all inputs)**
- **Test Suite Pass Rate**: **85 / 85 (100%)**

---

## 📄 License
This project is licensed under the MIT License.
