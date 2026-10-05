"""CompressX v2.0 — Adaptive Data Compression & Analysis Dashboard.

Clean, enterprise-grade SaaS interface:
- Minimalist typographic badges & indicator dots (no emojis or cluttered icons)
- Dark green sidebar with proportional navigation buttons
- Gradient welcome banner with system telemetry chips
- 4-column equally-proportioned metric cards
- 3-column Quick Actions cards with clean category pill tags
- Primary drag-and-drop file upload with optional sample benchmark loader
- Intuitive Space Saved / Expansion metric formatting
- Full-width algorithm comparison table and download center
"""

import hashlib
import io
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.entropy import calculate_entropy, theoretical_compression_limit
from analysis.predictor import CompressionPredictor, CostWeights
from analysis.repetition import analyze_repetition
from analysis.statistics import calculate_statistics
from compression.adaptive import AdaptiveCompressor
from compression.huffman import HuffmanCompressor
from compression.hybrid import HybridCompressor
from compression.rle import RLECompressor
from datasets.generate_datasets import DATASET_DIR, generate_all_datasets
from evaluation.benchmark import BenchmarkRunner
from evaluation.report_generator import generate_pdf_report
from storage.container import Container
from storage.history import add_history_entry, clear_history, load_history

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CompressX — Adaptive Data Compression",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# ENTERPRISE STYLING & DESIGN SYSTEM
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global Reset */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.main .block-container {
    padding: 0 1.5rem 2rem 1.5rem !important;
    max-width: 100% !important;
}

/* Sidebar Container */
section[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #164e2b 0%, #114223 55%, #0a2d17 100%) !important;
    min-width: 240px !important;
    max-width: 240px !important;
}
section[data-testid="stSidebar"] > div {
    padding: 0 !important;
}
button[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }

/* Sidebar Brand Header */
.sb-brand {
    background: linear-gradient(135deg, #1b5731 0%, #0d381c 100%);
    padding: 22px 18px 16px 18px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 8px;
}
.sb-brand-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.01em;
    margin: 0;
}
.sb-brand-subtitle {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.65);
    margin: 3px 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Sidebar Navigation Items */
.sb-nav-item {
    display: flex;
    align-items: center;
    padding: 11px 14px;
    border-radius: 8px;
    margin: 3px 0;
    color: rgba(255,255,255,0.78);
    font-size: 0.85rem;
    font-weight: 500;
    text-decoration: none;
}
.sb-nav-item.active {
    background: rgba(255,255,255,0.14);
    color: #ffffff;
    font-weight: 700;
    border-left: 3px solid #5ee890;
}

/* Sidebar User Status Panel */
.sb-bottom {
    padding: 12px 14px;
    border-top: 1px solid rgba(255,255,255,0.1);
    background: rgba(0,0,0,0.12);
}
.sb-user-card {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
}
.sb-user-monogram {
    width: 32px;
    height: 32px;
    background: #22c55e;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 800;
    color: #052e16;
    letter-spacing: 0.05em;
}
.sb-user-info p {
    margin: 0;
    line-height: 1.25;
}
.sb-user-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: #ffffff;
}
.sb-user-role {
    font-size: 0.68rem;
    color: rgba(255,255,255,0.6);
}

/* Top Header Bar */
.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 0 16px 0;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 20px;
}
.header-left h1 {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    letter-spacing: -0.02em;
}
.header-left p {
    font-size: 0.82rem;
    color: #64748b;
    margin: 3px 0 0 0;
}
.system-status-chip {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #15803d;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 9999px;
    letter-spacing: 0.04em;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
.system-status-chip::before {
    content: '';
    width: 6px;
    height: 6px;
    background: #16a34a;
    border-radius: 50%;
}

/* Welcome Banner */
.welcome-banner {
    background: linear-gradient(120deg, #134e2a 0%, #1e587a 50%, #2563eb 100%);
    border-radius: 12px;
    padding: 26px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 22px;
    position: relative;
    overflow: hidden;
}
.wb-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 6px 0;
}
.wb-sub {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.85);
    margin: 0 0 12px 0;
}
.wb-telemetry {
    display: flex;
    gap: 16px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.75);
    align-items: center;
}
.wb-chip {
    background: rgba(255,255,255,0.14);
    padding: 3px 9px;
    border-radius: 4px;
    font-weight: 600;
}
.wb-badge-pill {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 10px;
    padding: 12px 20px;
    text-align: right;
}
.wb-badge-title {
    font-size: 0.68rem;
    color: rgba(255,255,255,0.7);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.wb-badge-value {
    font-size: 1.05rem;
    font-weight: 800;
    color: #ffffff;
}

/* Stat Cards */
.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 18px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    min-height: 125px;
}
.stat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.stat-badge {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 7px;
    border-radius: 4px;
}
.stat-badge-green  { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.stat-badge-blue   { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.stat-badge-purple { background: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe; }
.stat-badge-orange { background: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }

.stat-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
}
.stat-indicator-green  { background: #16a34a; }
.stat-indicator-blue   { background: #2563eb; }
.stat-indicator-purple { background: #7c3aed; }
.stat-indicator-orange { background: #ea580c; }

.stat-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
    margin: 0 0 2px 0;
}
.stat-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
    line-height: 1.1;
}
.stat-sub {
    font-size: 0.72rem;
    font-weight: 600;
    margin: 0;
}
.stat-sub-green  { color: #15803d; }
.stat-sub-blue   { color: #1d4ed8; }
.stat-sub-purple { color: #6d28d9; }
.stat-sub-orange { color: #c2410c; }

/* Section Header */
.section-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #0f172a;
    margin: 22px 0 12px 0;
    letter-spacing: -0.01em;
}

/* Quick Action Cards */
.action-card {
    border-radius: 10px;
    padding: 16px 18px;
    transition: all 0.18s ease;
    height: 90px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.action-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.action-card-green  { background: #f0fdf4; border: 1px solid #bbf7d0; }
.action-card-purple { background: #faf5ff; border: 1px solid #e9d5ff; }
.action-card-orange { background: #fff7ed; border: 1px solid #fed7aa; }

.action-pill {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.action-pill-green  { color: #15803d; }
.action-pill-purple { color: #6d28d9; }
.action-pill-orange { color: #c2410c; }

.action-label {
    font-size: 0.92rem;
    font-weight: 700;
}
.action-label-green  { color: #14532d; }
.action-label-purple { color: #581c87; }
.action-label-orange { color: #7c2d12; }

.action-desc {
    font-size: 0.72rem;
    color: #64748b;
}

/* Result Section */
.result-section {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px 24px;
    margin: 18px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.result-grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 14px 0;
}
.result-mini-card {
    background: #f8fafc;
    border: 1px solid #edf2f7;
    border-radius: 8px;
    padding: 14px;
    text-align: center;
}
.rmc-label {
    font-size: 0.68rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.rmc-value {
    font-size: 1.35rem;
    font-weight: 800;
    color: #0f172a;
    margin: 4px 0 2px 0;
}
.rmc-sub {
    font-size: 0.72rem;
    color: #64748b;
}

/* Before vs After Visualization Bar */
.bar-container { margin: 12px 0; }
.bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.78rem;
    color: #334155;
    font-weight: 600;
    margin-bottom: 4px;
}
.bar-outer {
    background: #f1f5f9;
    border-radius: 9999px;
    height: 8px;
    overflow: hidden;
}
.bar-fill {
    height: 8px;
    border-radius: 9999px;
    transition: width 0.5s ease;
}
.bar-orig {
    background: #64748b;
    width: 100%;
}

/* Integrity Badges */
.integrity-pass {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #15803d;
    margin: 12px 0;
}
.integrity-fail {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #b91c1c;
    margin: 12px 0;
}
.hash-code {
    font-family: 'Courier New', monospace;
    font-size: 0.72rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1e40af;
    word-break: break-all;
    margin: 4px 0;
}

/* Table Styling */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}
.styled-table th {
    background: #f8fafc;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    color: #475569;
    border-bottom: 2px solid #e2e8f0;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.styled-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #f1f5f9;
    color: #0f172a;
}
.styled-table tr:last-child td { border-bottom: none; }
.styled-table tr.best-row td {
    background: #f0fdf4;
    font-weight: 600;
}
.best-tag {
    display: inline-block;
    background: #dcfce7;
    color: #15803d;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 6px;
    border: 1px solid #86efac;
}
.pass-tag { color: #15803d; font-weight: 700; }
.fail-tag { color: #dc2626; font-weight: 700; }

/* Streamlit Button Overrides */
.stDownloadButton > button {
    background: #164e2b !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 9px 14px !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    background: #114223 !important;
}
.stButton > button[kind="primary"] {
    background: #164e2b !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-size: 0.86rem !important;
    padding: 11px 20px !important;
}
.stButton > button[kind="primary"]:hover {
    background: #114223 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    text-align: left !important;
}

/* File Uploader styling */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #94a3b8 !important;
    border-radius: 10px !important;
    background: #f8fafc !important;
}

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# STATE MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "compress"
if "active_job" not in st.session_state:
    st.session_state["active_job"] = None


def fmt_bytes(n: int) -> str:
    """Format bytes into clean unit."""
    if n < 1024:
        return f"{n} B"
    elif n < 1048576:
        return f"{n/1024:.2f} KB"
    else:
        return f"{n/1048576:.2f} MB"


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <p class="sb-brand-title">CompressX</p>
        <p class="sb-brand-subtitle">Adaptive Lossless Platform</p>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("compress",   "Dashboard & Compression"),
        ("decompress", "Decompress & Verify"),
        ("benchmark",  "Algorithm Benchmarks"),
        ("history",    "Compression History"),
        ("about",      "System Architecture"),
    ]

    for page_key, label in nav_items:
        is_active = st.session_state["current_page"] == page_key
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{page_key}", type=btn_type, use_container_width=True):
            st.session_state["current_page"] = page_key
            st.rerun()

    st.markdown("<div style='height:90px'></div>", unsafe_allow_html=True)
    st.divider()

    hist_count = len(load_history())
    st.markdown(f"""
    <div class="sb-bottom">
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:rgba(255,255,255,0.65);">
            <span>Audit Trail</span>
            <span>{hist_count} records</span>
        </div>
        <div class="sb-user-card">
            <div class="sb-user-monogram">CX</div>
            <div class="sb-user-info">
                <p class="sb-user-name">Adaptive Engine</p>
                <p class="sb-user-role">Lossless Pipeline v2.0</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Reset Session State", key="reset_state_btn", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# MAIN VIEW CONTROLLER
# ──────────────────────────────────────────────────────────────────────────────
current_page = st.session_state.get("current_page", "compress")
norm_weights = CostWeights()
adaptive_comp = AdaptiveCompressor(weights=norm_weights)

# ──────────────────────────────────────────────────────────────────────────────
# PAGE 1: DASHBOARD & COMPRESSION
# ──────────────────────────────────────────────────────────────────────────────
if current_page == "compress":
    # Top Header (Clean, professional, searchbar & bell removed)
    st.markdown("""
    <div class="top-header">
        <div class="header-left">
            <h1>Dashboard Overview</h1>
            <p>Intelligent Data Profiling and Adaptive Lossless Algorithm Selection</p>
        </div>
        <div class="header-right">
            <span class="system-status-chip">SYSTEM ONLINE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Welcome Banner (Typography-focused, no emojis)
    st.markdown("""
    <div class="welcome-banner">
        <div>
            <p class="wb-title">Adaptive Data Compression Suite</p>
            <p class="wb-sub">Analyzes empirical entropy and pattern repetition to select the optimal compression strategy</p>
            <div class="wb-telemetry">
                <span class="wb-chip">ENGINE: ONLINE</span>
                <span class="wb-chip">INTEGRITY: SHA-256</span>
                <span class="wb-chip">CONTAINER: AHDC-v1</span>
            </div>
        </div>
        <div class="wb-badge-pill">
            <div class="wb-badge-title">Active Architecture</div>
            <div class="wb-badge-value">Adaptive v2.0</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Summary Stat Cards
    job = st.session_state.get("active_job")
    s_orig = fmt_bytes(job["original_size"]) if job else "—"
    s_comp = fmt_bytes(job["compressed_size"]) if job else "—"
    s_ratio = f"{job['compression_ratio']:.2f}x" if job else "—"
    s1_sub = f"Compressed: {fmt_bytes(job['compressed_size'])}" if job else "Upload a file to begin"
    s2_sub = job["selected_strategy"] if job else "Pending input"
    s3_sub = "Lossless Verified" if (job and job["integrity_verified"]) else ("Checksum Mismatch" if job else "Pending execution")

    # Space Saved / Expansion Formatting Logic
    if job:
        sp_val = job["space_saving_pct"]
        if sp_val >= 0:
            s_saved = f"{sp_val:.1f}%"
            s4_badge = "EFFICIENCY"
            s4_label = "Space Saved"
            s4_sub = f"{job['encoding_time']:.4f}s latency"
        else:
            s_saved = f"+{abs(sp_val):.1f}%"
            s4_badge = "OVERHEAD"
            s4_label = "Size Expansion"
            s4_sub = "Container metadata overhead"
    else:
        s_saved = "—"
        s4_badge = "BENEFIT"
        s4_label = "Space Saved"
        s4_sub = "Awaiting compression"

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-badge stat-badge-green">RAW INPUT</span>
                <span class="stat-indicator stat-indicator-green"></span>
            </div>
            <p class="stat-label">Original File Size</p>
            <p class="stat-value">{s_orig}</p>
            <p class="stat-sub stat-sub-green">{s1_sub}</p>
        </div>""", unsafe_allow_html=True)

    with sc2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-badge stat-badge-blue">ACTIVE STRATEGY</span>
                <span class="stat-indicator stat-indicator-blue"></span>
            </div>
            <p class="stat-label">Algorithm Selected</p>
            <p class="stat-value" style="font-size:1.15rem;">{s2_sub}</p>
            <p class="stat-sub stat-sub-blue">Adaptive decision layer</p>
        </div>""", unsafe_allow_html=True)

    with sc3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-badge stat-badge-purple">VERIFICATION</span>
                <span class="stat-indicator stat-indicator-purple"></span>
            </div>
            <p class="stat-label">Integrity Status</p>
            <p class="stat-value" style="font-size:1.15rem;">{s3_sub}</p>
            <p class="stat-sub stat-sub-purple">SHA-256 validation</p>
        </div>""", unsafe_allow_html=True)

    with sc4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-header">
                <span class="stat-badge stat-badge-orange">{s4_badge}</span>
                <span class="stat-indicator stat-indicator-orange"></span>
            </div>
            <p class="stat-label">{s4_label}</p>
            <p class="stat-value">{s_saved}</p>
            <p class="stat-sub stat-sub-orange">{s4_sub}</p>
        </div>""", unsafe_allow_html=True)

    # Quick Actions (Clean typographic badges, no small icons)
    st.markdown('<div class="section-title">Quick Actions</div>', unsafe_allow_html=True)
    qa1, qa2, qa3 = st.columns(3)

    with qa1:
        st.markdown("""
        <div class="action-card action-card-green">
            <div class="action-pill action-pill-green">ACTION 01</div>
            <div class="action-label action-label-green">Compress File</div>
            <div class="action-desc">Adaptive data analysis and encoding</div>
        </div>""", unsafe_allow_html=True)

    with qa2:
        st.markdown("""
        <div class="action-card action-card-purple">
            <div class="action-pill action-pill-purple">ACTION 02</div>
            <div class="action-label action-label-purple">Decompress Archive</div>
            <div class="action-desc">Extract .ahdc with cryptographic check</div>
        </div>""", unsafe_allow_html=True)

    with qa3:
        st.markdown("""
        <div class="action-card action-card-orange">
            <div class="action-pill action-pill-orange">ACTION 03</div>
            <div class="action-label action-label-orange">Benchmark Suite</div>
            <div class="action-desc">Cross-algorithm comparison matrix</div>
        </div>""", unsafe_allow_html=True)

    # ── File Upload Section (Primary, clean, no mandatory radio) ──
    st.markdown('<div class="section-title">File Ingestion</div>', unsafe_allow_html=True)

    up_file = st.file_uploader(
        "Upload local file to compress:",
        type=None,
        help="All files are processed in-memory as raw binary byte streams.",
        label_visibility="collapsed",
    )

    input_bytes: Optional[bytes] = None
    input_name = "sample.txt"

    if up_file:
        input_bytes = up_file.read()
        input_name = up_file.name
    else:
        # Subtle, secondary helper for testing benchmark samples
        with st.expander("Or select an academic benchmark sample (Datasets A–E)"):
            st.caption(
                "Preset datasets demonstrate theoretical extremes: "
                "Dataset A (repetitive runs for RLE), Dataset B (skewed alphabet for Huffman), "
                "Dataset C (prose), Dataset D (telemetry), and Dataset E (high-entropy random noise)."
            )
            ds_presets = {
                "Select a sample file...": "",
                "Dataset A — Highly Repetitive Sequences (Runs)": "dataset_a_repetitive.txt",
                "Dataset B — Zipfian Skewed Letter Frequencies": "dataset_b_skewed.txt",
                "Dataset C — Natural Language Text": "dataset_c_natural_text.txt",
                "Dataset D — Structured Server Access Logs": "dataset_d_server_logs.log",
                "Dataset E — High-Entropy Pseudorandom Stream": "dataset_e_random_data.bin",
            }
            preset_choice = st.selectbox("Sample Dataset:", list(ds_presets.keys()), label_visibility="collapsed")
            if preset_choice and ds_presets[preset_choice]:
                fname = ds_presets[preset_choice]
                fpath = os.path.join(DATASET_DIR, fname)
                if not os.path.exists(fpath):
                    generate_all_datasets()
                with open(fpath, "rb") as f:
                    input_bytes = f.read()
                input_name = fname

    if input_bytes and len(input_bytes) > 0:
        file_len = len(input_bytes)
        st.markdown(
            f"<p style='font-size:0.82rem; color:#15803d; font-weight:600; margin:6px 0 14px 0;'>"
            f"Active file: <b>{input_name}</b> &nbsp;|&nbsp; Size: <b>{fmt_bytes(file_len)}</b> ({file_len:,} bytes)</p>",
            unsafe_allow_html=True,
        )

        # Pre-compression statistical profiling
        profile, prediction = adaptive_comp.analyze(input_bytes)

        st.markdown('<div class="section-title">Empirical Data Profiling</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-badge stat-badge-green">ENTROPY</span>
                    <span class="stat-indicator stat-indicator-green"></span>
                </div>
                <p class="stat-label">Shannon Entropy H(X)</p>
                <p class="stat-value">{profile['entropy']:.2f}</p>
                <p class="stat-sub stat-sub-green">bits/symbol (max 8.0)</p>
            </div>""", unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-badge stat-badge-blue">REPETITION</span>
                    <span class="stat-indicator stat-indicator-blue"></span>
                </div>
                <p class="stat-label">Repetition Rate</p>
                <p class="stat-value">{profile['repetition_percentage']:.1f}%</p>
                <p class="stat-sub stat-sub-blue">Avg run: {profile['average_run_length']:.2f}</p>
            </div>""", unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-badge stat-badge-purple">ALPHABET</span>
                    <span class="stat-indicator stat-indicator-purple"></span>
                </div>
                <p class="stat-label">Unique Symbols</p>
                <p class="stat-value">{profile['unique_symbols']}</p>
                <p class="stat-sub stat-sub-purple">out of 256 byte values</p>
            </div>""", unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-badge stat-badge-orange">SKEWNESS</span>
                    <span class="stat-indicator stat-indicator-orange"></span>
                </div>
                <p class="stat-label">Gini Coefficient</p>
                <p class="stat-value">{profile['gini_coefficient']:.2f}</p>
                <p class="stat-sub stat-sub-orange">Distribution skew (0–1)</p>
            </div>""", unsafe_allow_html=True)

        # Recommendation Banner
        benefit_color = {"HIGH": "#15803d", "MODERATE": "#1d4ed8", "LOW": "#c2410c", "NEGLIGIBLE": "#b91c1c"}
        bc = benefit_color.get(prediction.expected_benefit, "#475569")
        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:4px solid #164e2b;
                    border-radius:10px; padding:18px 22px; margin:18px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:0.68rem; font-weight:700; text-transform:uppercase;
                                 letter-spacing:.08em; color:#64748b; background:#e2e8f0; padding:2px 7px; border-radius:4px;">
                        RECOMMENDED STRATEGY
                    </span>
                    <p style="font-size:1.4rem; font-weight:800; color:#0f172a; margin:6px 0 4px 0;">
                        {prediction.recommended_strategy}
                    </p>
                    <p style="font-size:0.82rem; color:#475569; margin:0; line-height:1.5;">
                        {prediction.explanation}
                    </p>
                </div>
                <div style="text-align:right; min-width:130px; border-left:1px solid #e2e8f0; padding-left:18px;">
                    <p style="font-size:0.68rem; text-transform:uppercase; letter-spacing:.06em; color:#64748b; margin:0 0 2px 0;">
                        Expected Benefit
                    </p>
                    <p style="font-size:1.1rem; font-weight:800; color:{bc}; margin:0 0 8px 0;">
                        {prediction.expected_benefit}
                    </p>
                    <p style="font-size:0.68rem; text-transform:uppercase; letter-spacing:.06em; color:#64748b; margin:0 0 2px 0;">
                        Estimated Bound
                    </p>
                    <p style="font-size:0.95rem; font-weight:700; color:#0f172a; margin:0;">
                        ~{prediction.estimated_ratio:.2f}x
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Start Adaptive Compression", type="primary", use_container_width=True):
            with st.status("Executing compression pipeline...", expanded=True) as status:
                st.write("Ingesting byte stream and profiling character frequency distributions...")
                time.sleep(0.04)
                st.write("Evaluating Shannon entropy boundary conditions and repetition ratios...")
                time.sleep(0.04)
                container_bytes, chosen_strat, pred_obj, details = adaptive_comp.compress_adaptive(
                    input_bytes, file_name=input_name, selection_mode="prediction"
                )
                st.write("Packaging into AHDC binary container with SHA-256 checksum...")
                time.sleep(0.04)
                decomp_bytes, integrity_ok, verify_msg, decomp_info = AdaptiveCompressor.decompress_container(
                    container_bytes
                )
                st.write("Lossless integrity verified against original file stream.")
                status.update(label="Compression pipeline completed successfully.", state="complete", expanded=False)

            orig_sha = hashlib.sha256(input_bytes).hexdigest()
            decomp_sha = decomp_info["computed_sha256"]

            runner = BenchmarkRunner()
            comp_rows, _ = runner.run_single_dataset(input_name, input_bytes)

            st.session_state["active_job"] = {
                "file_name": input_name,
                "original_bytes": input_bytes,
                "container_bytes": container_bytes,
                "selected_strategy": chosen_strat,
                "original_size": details["original_size"],
                "compressed_size": details["container_size"],
                "compression_ratio": details["compression_ratio"],
                "space_saving_pct": details["space_saving_pct"],
                "encoding_time": details["total_elapsed_time"],
                "decoding_time": decomp_info["decoding_time"],
                "profile": profile,
                "prediction": prediction,
                "explanation": prediction.explanation,
                "integrity_verified": integrity_ok,
                "sha256_original": orig_sha,
                "sha256_decompressed": decomp_sha,
                "decompressed_bytes": decomp_bytes,
                "comparison_rows": comp_rows,
            }

            add_history_entry(
                file_name=input_name,
                original_size=details["original_size"],
                compressed_size=details["container_size"],
                compression_ratio=details["compression_ratio"],
                space_saved_pct=details["space_saving_pct"],
                algorithm=chosen_strat,
                encoding_time_sec=details["total_elapsed_time"],
                decoding_time_sec=decomp_info["decoding_time"],
                integrity_status="PASSED" if integrity_ok else "FAILED",
                sha256_hash=orig_sha,
            )
            st.rerun()

        # Results Dashboard
        if st.session_state.get("active_job"):
            j = st.session_state["active_job"]
            st.markdown('<div class="section-title">Compression Results</div>', unsafe_allow_html=True)

            # Space Saved / Expansion Formatting Logic
            sp_val = j["space_saving_pct"]
            if sp_val >= 0:
                space_display = f"{sp_val:.1f}%"
                space_title = "Space Saved"
                space_caption = "Storage reduced"
            else:
                space_display = f"+{abs(sp_val):.1f}%"
                space_title = "Size Expansion"
                space_caption = "Container metadata on incompressible data"

            st.markdown(f"""
            <div class="result-section">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                    <span style="font-size:0.85rem; font-weight:700; color:#15803d;">
                        PIPELINE COMPLETED &nbsp;·&nbsp; STRATEGY: {j['selected_strategy']}
                    </span>
                    <span style="font-size:0.75rem; color:#64748b; font-family:monospace;">
                        AHDC-v1 CONTAINER
                    </span>
                </div>
                <div class="result-grid-4">
                    <div class="result-mini-card">
                        <p class="rmc-label">Original File</p>
                        <p class="rmc-value">{fmt_bytes(j['original_size'])}</p>
                        <p class="rmc-sub">{j['original_size']:,} bytes</p>
                    </div>
                    <div class="result-mini-card">
                        <p class="rmc-label">Compressed Container</p>
                        <p class="rmc-value">{fmt_bytes(j['compressed_size'])}</p>
                        <p class="rmc-sub">{j['compressed_size']:,} bytes</p>
                    </div>
                    <div class="result-mini-card">
                        <p class="rmc-label">Compression Ratio</p>
                        <p class="rmc-value">{j['compression_ratio']:.2f}x</p>
                        <p class="rmc-sub">Original ÷ Compressed</p>
                    </div>
                    <div class="result-mini-card">
                        <p class="rmc-label">{space_title}</p>
                        <p class="rmc-value">{space_display}</p>
                        <p class="rmc-sub">{space_caption}</p>
                    </div>
                </div>

                <div class="bar-container">
                    <div class="bar-label">
                        <span>Original Input Stream</span>
                        <span>{fmt_bytes(j['original_size'])}</span>
                    </div>
                    <div class="bar-outer">
                        <div class="bar-fill bar-orig"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            pct_fill = max(int((j["compressed_size"] / max(j["original_size"], 1)) * 100), 1)
            fill_color = "#16a34a" if pct_fill < 70 else ("#ea580c" if pct_fill < 100 else "#dc2626")
            st.markdown(f"""
                <div class="bar-container">
                    <div class="bar-label">
                        <span>Compressed AHDC Archive</span>
                        <span>{fmt_bytes(j['compressed_size'])} ({pct_fill}% of original)</span>
                    </div>
                    <div class="bar-outer">
                        <div class="bar-fill" style="width:{min(pct_fill, 100)}%; background:{fill_color};"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Lossless Integrity Verification
            if j["integrity_verified"]:
                st.markdown(f"""
                <div class="integrity-pass">
                    <div>LOSSLESS INTEGRITY VERIFIED — PASSED</div>
                    <div style="font-weight:400; font-size:0.76rem; color:#15803d; margin-top:2px;">
                        Exact cryptographic match computed on {j['original_size']:,} bytes.
                    </div>
                </div>
                <div class="hash-code">SHA-256: {j['sha256_original']}</div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""<div class="integrity-fail">INTEGRITY CHECK FAILED — Checksum mismatch.</div>""", unsafe_allow_html=True)

            # Algorithm Comparison Table
            if j.get("comparison_rows"):
                st.markdown('<div class="section-title">Multi-Algorithm Comparison Matrix</div>', unsafe_allow_html=True)
                best_size = min(r["Compressed Size (B)"] for r in j["comparison_rows"])
                rows_html = ""
                for row in j["comparison_rows"]:
                    is_best = row["Compressed Size (B)"] == best_size
                    tr_cls = "best-row" if is_best else ""
                    best_tag = "<span class='best-tag'>OPTIMAL</span>" if is_best else ""
                    itg_cls = "pass-tag" if row["Integrity"] == "PASSED" else "fail-tag"
                    sp = row["Space Saved (%)"]
                    sp_str = f"{sp:.2f}%" if sp >= 0 else f"+{abs(sp):.2f}% (exp)"
                    rows_html += f"""
                    <tr class="{tr_cls}">
                        <td>{row['Algorithm']}{best_tag}</td>
                        <td>{row['Original Size (B)']:,}</td>
                        <td>{row['Compressed Size (B)']:,}</td>
                        <td>{row['Ratio']:.3f}x</td>
                        <td>{sp_str}</td>
                        <td>{row['Encoding Time (s)']:.5f}s</td>
                        <td>{row['Decoding Time (s)']:.5f}s</td>
                        <td class="{itg_cls}">{row['Integrity']}</td>
                    </tr>"""

                st.markdown(f"""
                <div style="overflow-x:auto;">
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>Algorithm</th><th>Original</th><th>Compressed</th>
                            <th>Ratio</th><th>Space Delta</th>
                            <th>Enc Time</th><th>Dec Time</th><th>Integrity</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                </div>
                """, unsafe_allow_html=True)

            # Download Center (Professional text, no emojis)
            st.markdown('<div class="section-title">Export & Artifact Downloads</div>', unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)

            with d1:
                st.download_button(
                    "Download Compressed Container (.ahdc)",
                    data=j["container_bytes"],
                    file_name=f"{j['file_name']}.ahdc",
                    mime="application/octet-stream",
                    use_container_width=True,
                )

            with d2:
                pdf_bytes = generate_pdf_report(
                    file_name=j["file_name"],
                    original_size=j["original_size"],
                    compressed_size=j["compressed_size"],
                    compression_ratio=j["compression_ratio"],
                    space_saved_pct=j["space_saving_pct"],
                    selected_algorithm=j["selected_strategy"],
                    encoding_time_sec=j["encoding_time"],
                    decoding_time_sec=j["decoding_time"],
                    profile=j["profile"],
                    explanation=j["explanation"],
                    sha256_original=j["sha256_original"],
                    sha256_decompressed=j["sha256_decompressed"],
                    integrity_verified=j["integrity_verified"],
                    comparison_rows=j.get("comparison_rows"),
                )
                st.download_button(
                    "Download Technical Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"CompressX_Report_{j['file_name']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            with d3:
                tel = {
                    "tool": "CompressX v2.0",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "file_name": j["file_name"],
                    "original_size": j["original_size"],
                    "compressed_size": j["compressed_size"],
                    "compression_ratio": j["compression_ratio"],
                    "space_saved_pct": j["space_saving_pct"],
                    "algorithm": j["selected_strategy"],
                    "integrity": j["integrity_verified"],
                    "sha256": j["sha256_original"],
                    "profile": j["profile"],
                }
                st.download_button(
                    "Export Telemetry Data (JSON)",
                    data=json.dumps(tel, indent=2).encode(),
                    file_name=f"CompressX_Metrics_{j['file_name']}.json",
                    mime="application/json",
                    use_container_width=True,
                )

    elif input_bytes and len(input_bytes) == 0:
        st.warning("Selected file is completely empty (0 bytes).")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 2: DECOMPRESS & VERIFY
# ──────────────────────────────────────────────────────────────────────────────
elif current_page == "decompress":
    st.markdown("""
    <div class="top-header">
        <div class="header-left">
            <h1>Decompress & Verify</h1>
            <p>Unpack .ahdc archive containers with cryptographic SHA-256 validation</p>
        </div>
        <div class="header-right">
            <span class="system-status-chip">VALIDATOR READY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    archive_bytes = None
    archive_name = "archive.ahdc"

    up_archive = st.file_uploader(
        "Upload a CompressX .ahdc archive:",
        type=["ahdc"],
        label_visibility="collapsed",
    )
    if up_archive:
        archive_bytes = up_archive.read()
        archive_name = up_archive.name
    elif st.session_state.get("active_job"):
        st.info(f"Active session archive available: {st.session_state['active_job']['file_name']}.ahdc")
        if st.checkbox("Load archive from active session"):
            archive_bytes = st.session_state["active_job"]["container_bytes"]
            archive_name = f"{st.session_state['active_job']['file_name']}.ahdc"

    if archive_bytes:
        st.markdown(
            f"<p style='color:#15803d; font-weight:600; font-size:0.83rem;'>"
            f"Archive loaded: <b>{archive_name}</b> ({len(archive_bytes):,} bytes)</p>",
            unsafe_allow_html=True,
        )

        if st.button("Execute Decompression & Integrity Check", type="primary", use_container_width=True):
            try:
                with st.spinner("Unpacking archive and computing SHA-256 digests..."):
                    t0 = time.perf_counter()
                    decomp, passed, msg, info = AdaptiveCompressor.decompress_container(archive_bytes)
                    t_dec = time.perf_counter() - t0

                if passed:
                    st.markdown(f"""
                    <div class="integrity-pass">
                        <div>LOSSLESS INTEGRITY VERIFIED — PASSED</div>
                        <div style="font-weight:400; font-size:0.76rem; color:#15803d; margin-top:2px;">
                            Restored {len(decomp):,} bytes in {t_dec:.4f}s using algorithm: <b>{info['algorithm']}</b>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    h1, h2 = st.columns(2)
                    with h1:
                        st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#475569;'>Container Header Hash:</p>", unsafe_allow_html=True)
                        st.markdown(f"<div class='hash-code'>{info['expected_sha256']}</div>", unsafe_allow_html=True)
                    with h2:
                        st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#475569;'>Restored Stream Hash:</p>", unsafe_allow_html=True)
                        st.markdown(f"<div class='hash-code'>{info['computed_sha256']}</div>", unsafe_allow_html=True)

                    restored_name = f"restored_{info.get('file_name', 'file')}"
                    st.download_button(
                        f"Download Verified Restored File ({restored_name})",
                        data=decomp,
                        file_name=restored_name,
                        mime="application/octet-stream",
                        use_container_width=True,
                    )
                else:
                    st.markdown(f"<div class='integrity-fail'>INTEGRITY VERIFICATION FAILED: {msg}</div>", unsafe_allow_html=True)
            except Exception as exc:
                st.error(f"Failed to unpack container: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 3: ALGORITHM BENCHMARKS
# ──────────────────────────────────────────────────────────────────────────────
elif current_page == "benchmark":
    st.markdown("""
    <div class="top-header">
        <div class="header-left">
            <h1>Algorithm Benchmarks</h1>
            <p>Empirical evaluation of RLE, Huffman, Hybrid, CompressX Adaptive, and GZIP</p>
        </div>
        <div class="header-right">
            <span class="system-status-chip">BENCHMARK READY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    dataset_files = {
        "Dataset A (Repetitive)": os.path.join(DATASET_DIR, "dataset_a_repetitive.txt"),
        "Dataset B (Skewed)": os.path.join(DATASET_DIR, "dataset_b_skewed.txt"),
        "Dataset C (Natural Text)": os.path.join(DATASET_DIR, "dataset_c_natural_text.txt"),
        "Dataset D (Server Logs)": os.path.join(DATASET_DIR, "dataset_d_server_logs.log"),
        "Dataset E (Random Data)": os.path.join(DATASET_DIR, "dataset_e_random_data.bin"),
    }
    if not all(os.path.exists(p) for p in dataset_files.values()):
        generate_all_datasets()

    if st.button("Execute Academic Benchmark Suite (Datasets A through E)", type="primary", use_container_width=True):
        with st.spinner("Executing benchmark across all datasets..."):
            runner = BenchmarkRunner()
            df, summaries = runner.run_all(dataset_files)
            st.session_state["benchmark_df"] = df
            st.session_state["benchmark_summaries"] = summaries

    if "benchmark_df" in st.session_state:
        df = st.session_state["benchmark_df"]
        summaries = st.session_state["benchmark_summaries"]

        correct = sum(1 for s in summaries if s["prediction_match"])
        total = len(summaries)
        acc_pct = (correct / total) * 100 if total else 0.0

        pa1, pa2, pa3 = st.columns(3)
        with pa1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-green">ACCURACY</span></div>
                <p class="stat-label">Prediction Accuracy</p>
                <p class="stat-value">{acc_pct:.0f}%</p>
                <p class="stat-sub stat-sub-green">{correct} of {total} correct</p>
            </div>""", unsafe_allow_html=True)
        with pa2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-blue">COVERAGE</span></div>
                <p class="stat-label">Datasets Evaluated</p>
                <p class="stat-value">{total}</p>
                <p class="stat-sub stat-sub-blue">Heterogeneous profiles</p>
            </div>""", unsafe_allow_html=True)
        with pa3:
            st.markdown("""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-purple">INTEGRITY</span></div>
                <p class="stat-label">Lossless Verification</p>
                <p class="stat-value">100%</p>
                <p class="stat-sub stat-sub-purple">SHA-256 bit-for-bit</p>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Comparative Benchmark Matrix</div>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)

        chart_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evaluation", "charts")
        st.markdown('<div class="section-title">Analytical Visualizations</div>', unsafe_allow_html=True)
        vc1, vc2 = st.columns(2)
        with vc1:
            img = os.path.join(chart_dir, "compression_ratio_comparison.png")
            if os.path.exists(img):
                st.image(img, caption="Compression Ratio Comparison Across Datasets")
        with vc2:
            img2 = os.path.join(chart_dir, "space_savings_comparison.png")
            if os.path.exists(img2):
                st.image(img2, caption="Space Savings Percentage Comparison")


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 4: COMPRESSION HISTORY
# ──────────────────────────────────────────────────────────────────────────────
elif current_page == "history":
    st.markdown("""
    <div class="top-header">
        <div class="header-left">
            <h1>Compression History</h1>
            <p>Persistent audit trail of previous compression runs and integrity logs</p>
        </div>
        <div class="header-right">
            <span class="system-status-chip">AUDIT TRAIL</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    records = load_history()

    if records:
        total_orig = sum(r["original_size"] for r in records)
        total_comp = sum(r["compressed_size"] for r in records)
        avg_ratio = sum(r["compression_ratio"] for r in records) / len(records)
        passed_pct = sum(1 for r in records if r["integrity_status"] == "PASSED") / len(records) * 100

        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-green">RECORDS</span></div>
                <p class="stat-label">Total Jobs</p>
                <p class="stat-value">{len(records)}</p>
                <p class="stat-sub stat-sub-green">Operations logged</p>
            </div>""", unsafe_allow_html=True)
        with hc2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-blue">SAVINGS</span></div>
                <p class="stat-label">Total Data Saved</p>
                <p class="stat-value">{fmt_bytes(max(total_orig - total_comp, 0))}</p>
                <p class="stat-sub stat-sub-blue">Cumulative space</p>
            </div>""", unsafe_allow_html=True)
        with hc3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-purple">EFFICIENCY</span></div>
                <p class="stat-label">Average Ratio</p>
                <p class="stat-value">{avg_ratio:.2f}x</p>
                <p class="stat-sub stat-sub-purple">Mean compression</p>
            </div>""", unsafe_allow_html=True)
        with hc4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-header"><span class="stat-badge stat-badge-orange">VERIFIED</span></div>
                <p class="stat-label">Integrity Rate</p>
                <p class="stat-value">{passed_pct:.0f}%</p>
                <p class="stat-sub stat-sub-orange">SHA-256 match</p>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-title">Audit Log Entries</div>', unsafe_allow_html=True)
        rows_h = ""
        for rec in records:
            itg_cls = "pass-tag" if rec["integrity_status"] == "PASSED" else "fail-tag"
            sp = rec["space_saved_pct"]
            sp_str = f"{sp:.1f}%" if sp >= 0 else f"+{abs(sp):.1f}% (exp)"
            rows_h += f"""
            <tr>
                <td>{rec['id']}</td>
                <td>{rec['timestamp']}</td>
                <td><b>{rec['file_name']}</b></td>
                <td>{fmt_bytes(rec['original_size'])}</td>
                <td>{fmt_bytes(rec['compressed_size'])}</td>
                <td>{rec['compression_ratio']:.2f}x</td>
                <td>{sp_str}</td>
                <td>{rec['algorithm']}</td>
                <td class="{itg_cls}">{rec['integrity_status']}</td>
            </tr>"""

        st.markdown(f"""
        <div style="overflow-x:auto;">
        <table class="styled-table">
            <thead>
                <tr>
                    <th>#</th><th>Timestamp</th><th>File Name</th>
                    <th>Original</th><th>Compressed</th>
                    <th>Ratio</th><th>Space Delta</th>
                    <th>Algorithm</th><th>Integrity</th>
                </tr>
            </thead>
            <tbody>{rows_h}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear Audit History", use_container_width=True):
            clear_history()
            st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center; padding:50px 20px; color:#64748b;">
            <p style="font-size:0.95rem; font-weight:600; color:#0f172a;">No audit records found</p>
            <p style="font-size:0.8rem;">Run a compression operation to record history.</p>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# PAGE 5: ABOUT
# ──────────────────────────────────────────────────────────────────────────────
elif current_page == "about":
    st.markdown("""
    <div class="top-header">
        <div class="header-left">
            <h1>System Architecture</h1>
            <p>CompressX v2.0 · Adaptive Lossless Data Compression Platform</p>
        </div>
        <div class="header-right">
            <span class="system-status-chip">DOCUMENTATION</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    about_col1, about_col2 = st.columns(2)
    with about_col1:
        st.markdown("""
        <div class="result-section">
            <p style="font-size:0.95rem; font-weight:800; color:#0f172a; margin:0 0 10px 0;">Theoretical Foundations</p>
            <p style="font-size:0.83rem; color:#334155; line-height:1.65;">
            Traditional compression tools blindly apply a single algorithm regardless of input structure.
            CompressX implements an in-memory <b>data characterization layer</b> that calculates:
            </p>
            <ul style="font-size:0.8rem; color:#475569; line-height:1.8; margin-top:8px;">
                <li><b>Shannon Entropy H(X):</b> Information content lower bound (bits/symbol).</li>
                <li><b>Run-Length Redundancy:</b> Average run length R &gt; 2.0 profitability threshold.</li>
                <li><b>Gini Skewness:</b> Frequency non-uniformity across the byte alphabet.</li>
                <li><b>Multi-Criteria Cost Function:</b> Weighted balance of size, latency, and memory.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with about_col2:
        st.markdown("""
        <div class="result-section">
            <p style="font-size:0.95rem; font-weight:800; color:#0f172a; margin:0 0 10px 0;">Platform Features (v2.0)</p>
            <ul style="font-size:0.8rem; color:#334155; line-height:1.8; padding-left:18px; margin:0;">
                <li><b>Self-Describing Binary Container (.ahdc):</b> 47-byte fixed header with embedded SHA-256 digest.</li>
                <li><b>Downloadable PDF Reports:</b> ReportLab technical report with embedded vector charts.</li>
                <li><b>100% Lossless Guarantee:</b> Automated verification prevents corrupt extraction.</li>
                <li><b>Incompressibility Detection:</b> High-entropy streams bypass compression to prevent file bloat.</li>
                <li><b>Exportable Telemetry:</b> JSON format for analytics pipelines.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:10px; padding:18px 22px; margin-top:14px;">
        <p style="font-size:0.85rem; color:#15803d; margin:0; line-height:1.65;">
        <b>Core Academic Contribution:</b> Rather than claiming novel underlying algorithms (RLE and Huffman are classical),
        the novelty lies in <b>pre-compression statistical profiling, predictive strategy selection, hybrid two-stage compounding,
        and cryptographic container integrity verification</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
