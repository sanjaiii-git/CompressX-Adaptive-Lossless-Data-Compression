"""Unit tests for PDF report generation and history tracking."""

import os
import pytest
from evaluation.report_generator import generate_pdf_report
from storage.history import add_history_entry, clear_history, load_history


def test_pdf_report_generation():
    profile = {
        "entropy": 4.5,
        "repetition_percentage": 65.2,
        "average_run_length": 3.8,
        "unique_symbols": 42,
        "gini_coefficient": 0.48,
    }
    
    pdf_bytes = generate_pdf_report(
        file_name="test_sample.txt",
        original_size=10240,
        compressed_size=3450,
        compression_ratio=2.968,
        space_saved_pct=66.31,
        selected_algorithm="HYBRID (RLE + Huffman)",
        encoding_time_sec=0.01234,
        decoding_time_sec=0.00567,
        profile=profile,
        explanation="High repetition and frequency skew detected.",
        sha256_original="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        sha256_decompressed="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        integrity_verified=True,
    )
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes[:4] == b"%PDF"


def test_history_tracking():
    clear_history()
    assert load_history() == []
    
    entry = add_history_entry(
        file_name="demo.log",
        original_size=5000,
        compressed_size=2000,
        compression_ratio=2.5,
        space_saved_pct=60.0,
        algorithm="HUFFMAN",
        encoding_time_sec=0.01,
        decoding_time_sec=0.005,
        integrity_status="PASSED",
        sha256_hash="abc12345",
    )
    
    records = load_history()
    assert len(records) == 1
    assert records[0]["file_name"] == "demo.log"
    assert records[0]["algorithm"] == "HUFFMAN"
    
    clear_history()
    assert load_history() == []
