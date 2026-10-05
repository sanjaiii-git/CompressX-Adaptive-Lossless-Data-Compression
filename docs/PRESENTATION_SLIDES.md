# Presentation Deck: Adaptive Hybrid Data Compression Using Intelligent Algorithm Selection
**M.Tech Thesis / Project Defense**
**Candidate:** M.Tech Computer Science (Data Science)

---

## Slide 1: Title & Overview
- **Project Title:** Adaptive Hybrid Data Compression Using Intelligent Algorithm Selection
- **Domain:** Information Theory, Data Compression, Data Science
- **Core Novelty:** Pre-compression statistical profiling and explainable decision engine that replaces blind single-algorithm compression with adaptive multi-algorithm orchestration.

---

## Slide 2: Motivation & Problem Statement
- **Real-World Challenge:** In distributed cloud storage, IoT pipelines, and server telemetry, data streams are heterogeneous.
- **The Pitfall of Static Compression:**
  - RLE applied to normal text causes **100% file expansion** (size doubles!).
  - Huffman applied to repetitive streams achieves only ~2.6x instead of potential ~85x.
  - Applying compressors to encrypted/random data wastes CPU cycles without saving bytes.
- **Research Question:** *Can we analyze data characteristics prior to compression and automatically choose the winning strategy?*

---

## Slide 3: Proposed Architecture
- **Pipeline:**
  1. **Input Profiling:** Extract Shannon Entropy \(H(X)\), Average Run Length \(\bar{R}\), Repetition %, Gini Skew.
  2. **Intelligent Decision Engine:** Heuristic evaluation + Multi-Criteria Cost Function.
  3. **Candidate Execution:** RLE, Huffman, or sequential Hybrid (RLE \(\to\) Huffman).
  4. **Containerization:** Binary `.ahdc` format with embedded SHA-256 hash.
  5. **Lossless Verification:** Automated SHA-256 match check upon decompression.

---

## Slide 4: Theoretical Foundations
- **Shannon's Source Coding Theorem:**
  $$H(X) = - \sum_{i=1}^N p_i \log_2(p_i) \quad \implies \quad \bar{L} \ge H(X)$$
- **Mathematical Condition for RLE Profitability:**
  $$\text{Compressed Size} = 2 \cdot M < N \iff \bar{R} = \frac{N}{M} > 2.0$$
- **Prefix Coding & Kraft-McMillan Inequality:**
  $$\sum 2^{-\ell_i} \le 1$$
- **Multi-Criteria Optimization Function:**
  $$\text{Cost}(S) = 0.70 \cdot S_{\text{norm}} + 0.20 \cdot T_{\text{norm}} + 0.10 \cdot M_{\text{norm}}$$

---

## Slide 5: The Three Core Algorithms
1. **Run-Length Encoding (RLE):**
   - Collapses repeating runs into `(count, byte)` tuples.
   - Handles counts up to 255 per token; splits longer runs cleanly.
2. **Huffman Coding:**
   - Min-heap priority queue constructs optimal deterministic binary tree.
   - Custom bit-packing into byte stream with padding metadata.
3. **Hybrid RLE + Huffman:**
   - Two-stage pipeline: RLE compacts consecutive runs, then Huffman shrinks non-uniform frequency of run descriptors.
   - Decompressor reverses Huffman first, then reverses RLE.

---

## Slide 6: Self-Describing Container Format (.ahdc)
- **47-Byte Fixed Header:**
  - Magic Bytes: `AHDC`
  - Version: `0x01`
  - Algorithm ID: `0: RAW`, `1: RLE`, `2: HUFFMAN`, `3: HYBRID`
  - Original Size: 64-bit uint
  - Cryptographic SHA-256: 32 bytes binary digest
- **Variable JSON Metadata Block:** Tree frequencies, padding bits.
- **Payload:** Variable-length compressed bitstream.

---

## Slide 7: Experimental Datasets & Results
- **Evaluated on 5 Distinct 50 KB Benchmarks:**
  1. *Dataset A (Repetitive):* Hybrid achieved **85.19x ratio (98.83% saved)** vs RLE (63.68x) and Huffman (2.67x).
  2. *Dataset B (Skewed):* Huffman achieved **1.79x (43.97% saved)**. RLE collapsed (0.50x, size doubled).
  3. *Dataset C (Natural Text):* Huffman achieved **1.85x (45.87% saved)**. Adaptive selected Huffman correctly.
  4. *Dataset D (Server Logs):* Huffman achieved **1.59x (36.92% saved)**.
  5. *Dataset E (Random Noise):* Adaptive selected **NONE (Raw bypass)**, saving zero-overhead storage.
- **Overall Prediction Accuracy:** **100% (5/5 correct)**.
- **Lossless Verification:** **100% PASSED** across all edge cases (empty, single-byte, unicode, binary).

---

## Slide 8: Interactive Streamlit Demonstration
- **Features Demonstrated in Live Demo:**
  1. File Upload & Preset Dataset Selection.
  2. Real-time metric cards (Entropy, Repetition, Run Lengths).
  3. Explainable recommendation banner with confidence rating.
  4. Adaptive compression into `.ahdc` container with instant download.
  5. Decompression with side-by-side SHA-256 match confirmation.
  6. Visual benchmark comparisons (Bar charts & Scatter plots).

---

## Slide 9: Conclusion & Academic Contributions
- Successfully designed, implemented, and verified an **Adaptive Lossless Data Compression System**.
- Proved that statistical characterization before compression eliminates algorithmic mismatch and file expansion.
- Demonstrated that Hybrid RLE+Huffman significantly outperforms pure RLE on repetitive data.
- Codebase is 100% pure Python, completely transparent, reproducible, and mathematically grounded.
