"""Dataset generator for academic evaluation of the Adaptive Compression System.

Generates five distinct benchmark datasets with targeted statistical characteristics:
- Dataset A (repetitive.txt): Long continuous runs, high repetition, low runs count.
- Dataset B (skewed.txt): Extreme non-uniform symbol frequencies without long runs.
- Dataset C (natural_text.txt): Standard natural language text (articles, prose).
- Dataset D (server_logs.log): Structured server access and application logs with timestamps.
- Dataset E (random_data.bin): Pseudo-random high-entropy byte stream (near 8.0 bits/symbol).
"""

import os
import random

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_dataset_a(file_path: str, size_kb: int = 50) -> None:
    """Generate Dataset A: Highly repetitive data."""
    symbols = [b"A", b"B", b"C", b"D", b"0", b"9", b"-", b"#"]
    target_bytes = size_kb * 1024
    content = bytearray()

    while len(content) < target_bytes:
        sym = random.choice(symbols)
        run_len = random.randint(30, 200)
        content.extend(sym * run_len)

    content = content[:target_bytes]
    with open(file_path, "wb") as f:
        f.write(content)


def generate_dataset_b(file_path: str, size_kb: int = 50) -> None:
    """Generate Dataset B: Skewed frequency distribution with short runs."""
    # Zipfian / power-law distribution over alphabet
    # Frequent letters like 'e', 't', 'a', 'o', 'i', 'n'
    letters = b"etaoinshrdlcumwfgypbvkjxqz "
    weights = [26 - i for i in range(len(letters))]
    total_w = sum(weights)
    norm_weights = [w / total_w for w in weights]

    target_bytes = size_kb * 1024
    # Generate bytes with no consecutive identical symbols
    content = bytearray()
    last_b = None
    while len(content) < target_bytes:
        b = random.choices(letters, weights=norm_weights, k=1)[0]
        if b != last_b:
            content.append(b)
            last_b = b

    with open(file_path, "wb") as f:
        f.write(content)


def generate_dataset_c(file_path: str, size_kb: int = 50) -> None:
    """Generate Dataset C: Natural English prose and technical documentation."""
    sample_text = (
        "Adaptive data compression is an advanced topic in computer science and information theory. "
        "Lossless compression algorithms exploit redundancy within the source data to represent information "
        "using fewer bits than the uncompressed original. Classical Run-Length Encoding replaces consecutive "
        "identical symbols with a count and symbol descriptor, achieving optimal ratios on highly clustered "
        "data. In contrast, Huffman coding constructs a prefix tree based on the probability distribution of "
        "individual characters, approaching the theoretical Shannon entropy limit. The proposed adaptive "
        "hybrid architecture introduces an intelligent statistical decision engine that profiles input streams "
        "prior to compression, dynamically choosing the optimal strategy among RLE, Huffman, and a pipelined "
        "Hybrid configuration to balance compression ratio, execution latency, and memory consumption.\n"
    )
    target_bytes = size_kb * 1024
    encoded = sample_text.encode("utf-8")
    repetitions = (target_bytes // len(encoded)) + 1
    content = (encoded * repetitions)[:target_bytes]

    with open(file_path, "wb") as f:
        f.write(content)


def generate_dataset_d(file_path: str, size_kb: int = 50) -> None:
    """Generate Dataset D: Structured server logs and CSV telemetry."""
    ips = ["192.168.1.10", "10.0.0.15", "172.16.0.42", "127.0.0.1", "192.168.0.100"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    endpoints = ["/api/v1/auth", "/index.html", "/static/css/main.css", "/api/v1/users", "/health"]
    statuses = ["200", "201", "304", "400", "404", "500"]

    lines = []
    current_size = 0
    target_bytes = size_kb * 1024

    idx = 1000
    while current_size < target_bytes:
        line = (
            f"2026-10-05T14:{idx % 60:02d}:{idx % 60:02d}Z "
            f"ip={random.choice(ips)} "
            f"method={random.choice(methods)} "
            f"path={random.choice(endpoints)} "
            f"status={random.choice(statuses)} "
            f"latency_ms={random.randint(5, 250)}\n"
        )
        b_line = line.encode("utf-8")
        lines.append(b_line)
        current_size += len(b_line)
        idx += 1

    content = b"".join(lines)[:target_bytes]
    with open(file_path, "wb") as f:
        f.write(content)


def generate_dataset_e(file_path: str, size_kb: int = 50) -> None:
    """Generate Dataset E: High-entropy pseudo-random bytes (incompressible)."""
    target_bytes = size_kb * 1024
    # Using linear congruential pseudorandom sequence for reproducible uniform distribution
    content = bytearray(random.getrandbits(8) for _ in range(target_bytes))
    with open(file_path, "wb") as f:
        f.write(content)


def generate_all_datasets() -> dict:
    """Generate all 5 benchmark datasets and return paths."""
    os.makedirs(DATASET_DIR, exist_ok=True)
    datasets = {
        "Dataset A (Repetitive)": os.path.join(DATASET_DIR, "dataset_a_repetitive.txt"),
        "Dataset B (Skewed)": os.path.join(DATASET_DIR, "dataset_b_skewed.txt"),
        "Dataset C (Natural Text)": os.path.join(DATASET_DIR, "dataset_c_natural_text.txt"),
        "Dataset D (Server Logs)": os.path.join(DATASET_DIR, "dataset_d_server_logs.log"),
        "Dataset E (Random Data)": os.path.join(DATASET_DIR, "dataset_e_random_data.bin"),
    }

    random.seed(42)
    generate_dataset_a(datasets["Dataset A (Repetitive)"])
    generate_dataset_b(datasets["Dataset B (Skewed)"])
    generate_dataset_c(datasets["Dataset C (Natural Text)"])
    generate_dataset_d(datasets["Dataset D (Server Logs)"])
    generate_dataset_e(datasets["Dataset E (Random Data)"])

    print("All benchmark datasets generated successfully:")
    for name, path in datasets.items():
        print(f"  - {name}: {os.path.getsize(path)} bytes -> {path}")

    return datasets


if __name__ == "__main__":
    generate_all_datasets()
