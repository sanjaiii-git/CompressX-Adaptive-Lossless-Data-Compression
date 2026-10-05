# Comprehensive Viva Voce Questions & Answers Guide
**Subject:** Adaptive Hybrid Data Compression Using Intelligent Algorithm Selection
**Level:** M.Tech Computer Science / Data Science

---

### Q1: What is the main research contribution or novelty of your project?
**Answer:**
The novelty does **not** lie in inventing RLE or Huffman coding—both are classical, well-established algorithms.
The main contribution is the **Intelligent Adaptive Decision Layer**. Traditional tools statically apply a single compression scheme. Our system acts as an expert orchestrator that analyzes uncompressed data streams *in-memory*, computes empirical information-theoretic properties (Shannon entropy, run lengths, frequency distribution skewness), predicts the optimal strategy using an explainable multi-criteria cost model, executes the chosen algorithm, and stores the output in a custom container with cryptographic integrity verification.

---

### Q2: What is Shannon Entropy and how does it determine compressibility?
**Answer:**
Shannon Entropy \(H(X)\) measures the average amount of information or uncertainty in a random variable:
$$H(X) = - \sum_{i=1}^{N} p_i \log_2(p_i) \quad \text{bits/symbol}$$
For byte data (\(0\) to \(255\)), the maximum possible entropy is \(\log_2(256) = 8.0\) bits/symbol.
According to Shannon's Source Coding Theorem, no lossless code can achieve an average length less than \(H(X)\). If \(H(X) \approx 8.0\) (as in encrypted or pseudorandom data), there is virtually zero statistical redundancy to exploit. Conversely, if \(H(X) < 5.0\), significant redundancy exists, making Huffman coding highly effective.

---

### Q3: When does Run-Length Encoding fail, and what is its exact mathematical profitability condition?
**Answer:**
In standard byte-pair RLE, each run of \(k\) bytes (\(1 \le k \le 255\)) is stored as 2 bytes: `[count, byte_val]`.
If a file has \(N\) bytes and is segmented into \(M\) distinct runs, the RLE compressed size is \(2 \cdot M\) bytes.
RLE achieves compression (\(2M < N\)) if and only if the **average run length** \(\bar{R} = \frac{N}{M} > 2.0\).
If \(\bar{R} < 2.0\) (such as in natural English text or random data where \(\bar{R} \approx 1.0\)), RLE causes **file expansion of up to 100%** (size doubles). Our decision engine calculates \(\bar{R}\) before compressing, completely preventing this failure mode.

---

### Q4: Why combine RLE and Huffman into a Hybrid pipeline?
**Answer:**
RLE and Huffman target different types of redundancy:
- **RLE** exploits *consecutive local correlation* (long runs of identical symbols).
- **Huffman** exploits *global non-uniformity* (frequency skew across the alphabet).
When highly clustered data is passed through RLE, runs become a stream of `[count, symbol]` tokens. This intermediate stream still contains non-uniform symbol and count distributions. Applying Huffman coding on top of the RLE stream compresses these tokens further into variable-length prefix bits.
In our experiments on Dataset A, pure RLE achieved a **63.68x** ratio, while the Hybrid pipeline achieved an astounding **85.19x** ratio (a further 25% relative reduction).

---

### Q5: How did you implement Huffman coding without using external libraries?
**Answer:**
We implemented Huffman coding entirely from first principles using Python's standard library:
1. `collections.Counter` to calculate symbol frequencies.
2. `heapq` (priority min-heap) to greedily merge the two lowest-frequency trees into parent nodes. A deterministic tie-breaker counter is used so nodes with identical frequencies compare stably.
3. Recursive tree traversal to assign `'0'` to left branches and `'1'` to right branches.
4. Edge-case handling: For a single unique symbol (e.g. `b"AAAAA"`), a single leaf tree is formed and assigned code `'0'`.
5. Bit packing: The resulting bitstream is padded with \(P\) bits (\(0 \le P \le 7\)) to align with byte boundaries, and converted to packed bytes.
6. The exact symbol frequencies and padding count are serialized in the `.ahdc` container header to reconstruct the tree on decompression.

---

### Q6: How does the system handle incompressible or random data?
**Answer:**
Our predictor measures Shannon entropy \(H(X)\) and repetition percentage. On pseudorandom data (Dataset E), the entropy measured **7.9964 bits/symbol** (out of 8.0) and repetition was \(< 1\%\).
The decision engine recognized that applying compression would either yield 0% savings or cause file expansion due to metadata overhead. The system automatically recommended `NONE` (Raw Storage mode), packaging the raw bytes into the `.ahdc` container with zero expansion overhead.

---

### Q7: What is the purpose of your custom `.ahdc` binary container?
**Answer:**
A realistic compression utility cannot simply output raw bitstreams; it must be self-describing. Our `.ahdc` container includes:
1. **Magic bytes:** `b'AHDC'` for file type recognition.
2. **Version:** `0x01` for forward compatibility.
3. **Algorithm ID:** Indicating whether RLE, Huffman, Hybrid, or Raw mode was used.
4. **Original size:** 64-bit integer to prevent truncation.
5. **Original SHA-256 hash:** 32-byte cryptographic digest for integrity verification.
6. **Metadata block:** JSON-encoded frequency dictionary and bit padding count.
7. **Payload:** The actual algorithm-encoded bitstream.

---

### Q8: How do you mathematically guarantee that your system is lossless?
**Answer:**
We verify lossless integrity through two independent mechanisms:
1. **Cryptographic verification:** Before compression, the SHA-256 digest \(H_{\text{orig}}\) is computed and stored in the archive header. After decompression, the SHA-256 digest \(H_{\text{decomp}}\) of the restored stream is computed. If \(H_{\text{orig}} == H_{\text{decomp}}\), the file is mathematically proven to be identical with a collision probability less than \(2^{-256}\).
2. **Byte-by-byte comparison:** In our automated test suite (`tests/test_integrity.py`), `decompressed_bytes == original_bytes` is asserted across all edge cases (empty bytes, single byte, unicode, all 256 byte values, large buffers). All 35 tests pass with 100% success.

---

### Q9: Why is GZIP faster or smaller on some text files compared to Huffman?
**Answer:**
GZIP uses the **DEFLATE** algorithm, which combines **LZ77** (dictionary-based compression that replaces repeated substrings/phrases with back-references `(distance, length)`) and Huffman coding.
Huffman alone operates at the single-character / byte level without sliding window phrase matching. Therefore, on structured text or logs with repetitive multi-word phrases (e.g. `2026-10-05T14:`), LZ77 finds phrase matches that pure Huffman cannot.
We explicitly evaluated GZIP as an external baseline in our report to highlight the distinction between statistical symbol coding (Huffman) and dictionary coding (LZ77).

---

### Q10: How are the weights chosen in your multi-criteria cost function?
**Answer:**
The cost function evaluates:
$$\text{Cost} = w_{\text{size}} \cdot S_{\text{norm}} + w_{\text{time}} \cdot T_{\text{norm}} + w_{\text{mem}} \cdot M_{\text{norm}}$$
By default, \(w_{\text{size}} = 0.70\) prioritizes storage reduction (the primary goal of compression), \(w_{\text{time}} = 0.20\) penalizes slow encoding algorithms, and \(w_{\text{mem}} = 0.10\) accounts for working memory. The weights are completely configurable via sliders in the Streamlit UI, allowing the user to tune the system for latency-sensitive environments (e.g., real-time network transmission) or storage-critical environments (e.g., archival storage).
