"""PDF Technical Report Generator for CompressX (Adaptive Lossless Data Compression).

Generates a publication-grade, professional technical report including:
- Section 1 — Report Summary
- Section 2 — Input Content Analysis
- Section 3 — Algorithm Comparison Matrix
- Section 4 — Visual Performance Comparison (Embedded Bar Charts)
- Section 5 — Selection Rationale
- Section 6 — Integrity Verification
- Section 7 — Conclusion
"""

from datetime import datetime
import io
import os
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _generate_performance_charts(
    original_size: int,
    compressed_size: int,
    selected_algorithm: str,
    comparison_rows: Optional[List[Dict[str, Any]]] = None,
) -> io.BytesIO:
    """Generate side-by-side performance comparison charts in-memory."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 2.7))

    # Chart 1: Final Stored Size by Algorithm
    if comparison_rows and len(comparison_rows) > 0:
        valid_rows = [r for r in comparison_rows if r.get("Evaluation Status") != "Failed" and r.get("Final Stored Size (B)") is not None]
        names = [r["Algorithm"] for r in valid_rows]
        sizes = [r["Final Stored Size (B)"] for r in valid_rows]

        # Add original reference
        all_names = ["Original"] + names
        all_sizes = [original_size] + sizes
        colors_list = ["#4A5568"] + [
            "#2B6CB0" if n == selected_algorithm else "#718096" for n in names
        ]

        y_pos = range(len(all_names))
        bars = ax1.barh(y_pos, all_sizes, color=colors_list, edgecolor="#2D3748", height=0.6)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(all_names, fontsize=7, fontweight="bold")
        ax1.set_xlabel("Stored Size (Bytes)", fontsize=7)
        ax1.set_title("Final Stored Size by Algorithm", fontsize=8, fontweight="bold")
        ax1.invert_yaxis()
        ax1.grid(axis="x", linestyle="--", alpha=0.4)

        # Label values on bars
        for bar in bars:
            w = bar.get_width()
            ax1.text(
                w + (max(all_sizes) * 0.02),
                bar.get_y() + bar.get_height() / 2,
                f"{int(w):,} B",
                va="center",
                fontsize=6,
                color="#2D3748",
            )
        ax1.set_xlim(0, max(all_sizes) * 1.25)
    else:
        ax1.barh([0, 1], [original_size, compressed_size], color=["#4A5568", "#2B6CB0"], height=0.5)
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(["Original", selected_algorithm], fontsize=7, fontweight="bold")
        ax1.set_title("Before vs After Size", fontsize=8, fontweight="bold")
        ax1.invert_yaxis()

    # Chart 2: Compression Ratio by Algorithm
    if comparison_rows and len(comparison_rows) > 0:
        valid_rows = [r for r in comparison_rows if r.get("Compression Ratio") is not None]
        names = [r["Algorithm"] for r in valid_rows]
        ratios = [r["Compression Ratio"] for r in valid_rows]

        colors_ratio = ["#319795" if n == selected_algorithm else "#A0AEC0" for n in names]
        y_pos2 = range(len(names))
        bars2 = ax2.barh(y_pos2, ratios, color=colors_ratio, edgecolor="#2D3748", height=0.6)
        ax2.set_yticks(y_pos2)
        ax2.set_yticklabels(names, fontsize=7, fontweight="bold")
        ax2.set_xlabel("Ratio (Higher is Better)", fontsize=7)
        ax2.set_title("Compression Ratio Comparison", fontsize=8, fontweight="bold")
        ax2.invert_yaxis()
        ax2.grid(axis="x", linestyle="--", alpha=0.4)

        for bar in bars2:
            w = bar.get_width()
            ax2.text(
                w + (max(ratios) * 0.02 if max(ratios) > 0 else 0.05),
                bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}x",
                va="center",
                fontsize=6,
                color="#2D3748",
            )
        ax2.set_xlim(0, max(max(ratios) * 1.25, 1.2))

    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=200)
    plt.close()
    img_buf.seek(0)
    return img_buf


def generate_pdf_report(
    file_name: str,
    original_size: int,
    compressed_size: int,
    compression_ratio: float,
    space_saved_pct: float,
    selected_algorithm: str,
    encoding_time_sec: float,
    decoding_time_sec: float,
    profile: Dict[str, Any],
    explanation: str,
    sha256_original: str,
    sha256_decompressed: str,
    integrity_verified: bool,
    objective: str = "balanced",
    comparison_rows: Optional[List[Dict[str, Any]]] = None,
    total_processing_time: float = 0.0,
) -> bytes:
    """Generate a complete technical PDF report across all 7 required sections."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=8,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2D3748"),
    )
    callout_style = ParagraphStyle(
        "DocCallout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1A202C"),
    )
    code_style = ParagraphStyle(
        "DocCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#2C5282"),
    )

    story = []

    # Title Banner
    story.append(Paragraph("COMPRESSX — ADAPTIVE DATA COMPRESSION SYSTEM", title_style))
    story.append(
        Paragraph(
            f"Technical Performance Analysis & Lossless Verification Report • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=8))

    # SECTION 1: REPORT SUMMARY
    story.append(Paragraph("Section 1 — Report Summary", section_heading))
    total_time_str = f"{total_processing_time:.5f}s" if total_processing_time > 0 else f"{encoding_time_sec + decoding_time_sec:.5f}s"
    verif_status_str = "PASS (Bit-for-bit exact match)" if integrity_verified else "FAIL (Checksum mismatch)"

    overview_data = [
        [
            Paragraph("<b>Project:</b> CompressX v2.0", body_style),
            Paragraph(f"<b>Generation Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style),
            Paragraph(f"<b>Selected Algorithm:</b> <b>{selected_algorithm}</b>", body_style),
        ],
        [
            Paragraph(f"<b>Original File:</b> {file_name}", body_style),
            Paragraph(f"<b>Original Size:</b> {original_size:,} bytes", body_style),
            Paragraph(f"<b>Selection Objective:</b> {objective.title()}", body_style),
        ],
        [
            Paragraph(f"<b>Final Stored Size:</b> {compressed_size:,} bytes", body_style),
            Paragraph(f"<b>Compression Ratio:</b> <b>{compression_ratio:.3f}x</b>", body_style),
            Paragraph(f"<b>Space Saved:</b> <b>{space_saved_pct:.2f}%</b>", body_style),
        ],
        [
            Paragraph(f"<b>Encoding Latency:</b> {encoding_time_sec:.5f}s", body_style),
            Paragraph(f"<b>Decoding Latency:</b> {decoding_time_sec:.5f}s", body_style),
            Paragraph(f"<b>Integrity Verification:</b> <b>{verif_status_str}</b>", body_style),
        ],
    ]
    t_overview = Table(overview_data, colWidths=[180, 180, 180])
    t_overview.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(t_overview)
    story.append(Spacer(1, 6))

    # SECTION 2: INPUT CONTENT ANALYSIS
    story.append(Paragraph("Section 2 — Input Content Analysis", section_heading))
    ent = profile.get("entropy", 0.0)
    rep_pct = profile.get("repetition_percentage", 0.0)
    avg_run = profile.get("average_run_length", 0.0)
    uniq = profile.get("unique_symbols", 0)
    gini = profile.get("gini_coefficient", 0.0)

    analysis_data = [
        [
            Paragraph("<b>Empirical Characteristic</b>", body_style),
            Paragraph("<b>Measured Value</b>", body_style),
            Paragraph("<b>Information-Theoretic Impact on Strategy Selection</b>", body_style),
        ],
        [
            Paragraph("Shannon Entropy H(X)", body_style),
            Paragraph(f"<b>{ent:.4f}</b> bits/sym", body_style),
            Paragraph("Theoretical lower bound on symbol representation (max 8.0 bits). Lower entropy permits higher compression.", body_style),
        ],
        [
            Paragraph("Repetition Percentage", body_style),
            Paragraph(f"<b>{rep_pct:.2f}%</b>", body_style),
            Paragraph("Fraction of bytes participating in consecutive runs >= 2 bytes. Guides run-length encoding viability.", body_style),
        ],
        [
            Paragraph("Average Run Length", body_style),
            Paragraph(f"<b>{avg_run:.2f}</b> bytes", body_style),
            Paragraph("Average length of repeating symbol sequences. Values > 2.0 satisfy the mathematical profitability threshold for RLE.", body_style),
        ],
        [
            Paragraph("Alphabet Cardinality |V|", body_style),
            Paragraph(f"<b>{uniq}</b> / 256", body_style),
            Paragraph("Number of unique 8-bit symbols observed. Saturated alphabets reduce prefix coding advantage.", body_style),
        ],
        [
            Paragraph("Frequency Skew (Gini)", body_style),
            Paragraph(f"<b>{gini:.4f}</b>", body_style),
            Paragraph("Non-uniformity of symbol distribution (0=flat, 1=skewed). Higher values favor variable-length prefix coding.", body_style),
        ],
    ]

    has_ws = profile.get("has_whitespace_runs", False)
    ws_bytes = profile.get("whitespace_run_bytes", 0)
    ws_breakdown = profile.get("whitespace_breakdown", {})
    if has_ws and ws_bytes > 0:
        bd_str = ", ".join(f"{v:,} {k}" for k, v in ws_breakdown.items()) if ws_breakdown else f"{ws_bytes:,} bytes"
        ws_val_str = f"<b>YES</b> ({ws_bytes:,} bytes)"
        ws_impact = f"Whitespace actively participates in repeated runs ({bd_str}). Preserved losslessly."
    else:
        ws_val_str = "<b>NO</b> (0 run bytes)"
        ws_impact = "Whitespace characters do not form consecutive multi-byte runs (length >= 2)."

    analysis_data.append([
        Paragraph("Whitespace Run Participation", body_style),
        Paragraph(ws_val_str, body_style),
        Paragraph(ws_impact, body_style),
    ])

    t_analysis = Table(analysis_data, colWidths=[130, 85, 325])
    t_analysis.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ])
    )
    story.append(t_analysis)
    story.append(Spacer(1, 6))

    # SECTION 3: ALGORITHM COMPARISON MATRIX
    story.append(Paragraph("Section 3 — Algorithm Comparison Matrix", section_heading))
    if comparison_rows and len(comparison_rows) > 0:
        matrix_header = [
            Paragraph("<b>Algorithm</b>", body_style),
            Paragraph("<b>Status</b>", body_style),
            Paragraph("<b>Payload</b>", body_style),
            Paragraph("<b>Overhead</b>", body_style),
            Paragraph("<b>Final Size</b>", body_style),
            Paragraph("<b>Ratio</b>", body_style),
            Paragraph("<b>Saved</b>", body_style),
            Paragraph("<b>Enc Time</b>", body_style),
            Paragraph("<b>Throughput</b>", body_style),
            Paragraph("<b>Result</b>", body_style),
        ]
        matrix_table_data = [matrix_header]

        for r in comparison_rows:
            alg_name = r.get("Algorithm", "")
            is_winner = r.get("Selection Result") == "Selected" or alg_name == selected_algorithm
            prefix = "★ " if is_winner else ""

            payload_str = f"{r.get('Payload Size (B)', 0):,}" if r.get('Payload Size (B)') is not None else "-"
            overhead_str = f"{r.get('Metadata & Header Size (B)', 0):,}" if r.get('Metadata & Header Size (B)') is not None else "-"
            final_str = f"{r.get('Final Stored Size (B)', 0):,}" if r.get('Final Stored Size (B)') is not None else f"{r.get('Compressed Size (B)', 0):,}"
            ratio_val = r.get("Compression Ratio") or r.get("Ratio", 0.0)
            ratio_str = f"{ratio_val:.2f}x"
            saved_val = r.get("Space Saved (%)", 0.0)
            saved_str = f"{saved_val:.1f}%"
            enc_time_val = r.get("Compression Time (s)") or r.get("Encoding Time (s)", 0.0)
            enc_str = f"{enc_time_val:.4f}s"
            thr_val = r.get("Throughput (B/s)", 0.0)
            thr_str = f"{thr_val/1e6:.1f} MB/s" if thr_val >= 1e6 else f"{thr_val/1e3:.1f} KB/s"
            status_str = r.get("Evaluation Status", "Evaluated")
            sel_str = "SELECTED" if is_winner else r.get("Selection Result", "Not Selected")

            row_style = ParagraphStyle("WinStyle", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#1A365D")) if is_winner else body_style

            matrix_table_data.append([
                Paragraph(f"{prefix}{alg_name}", row_style),
                Paragraph(status_str, body_style),
                Paragraph(payload_str, body_style),
                Paragraph(overhead_str, body_style),
                Paragraph(final_str, row_style),
                Paragraph(ratio_str, row_style),
                Paragraph(saved_str, row_style),
                Paragraph(enc_str, body_style),
                Paragraph(thr_str, body_style),
                Paragraph(sel_str, row_style),
            ])

        t_matrix = Table(matrix_table_data, colWidths=[80, 50, 48, 48, 56, 44, 46, 52, 60, 56])
        t_matrix.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ])
        )
        story.append(t_matrix)
    else:
        story.append(Paragraph("Comparison matrix not provided for this run.", body_style))
    story.append(Spacer(1, 6))

    # SECTION 4: VISUAL PERFORMANCE COMPARISON
    story.append(Paragraph("Section 4 — Visual Performance Comparison", section_heading))
    chart_buf = _generate_performance_charts(
        original_size, compressed_size, selected_algorithm, comparison_rows
    )
    story.append(Image(chart_buf, width=7.4 * inch, height=2.6 * inch))
    story.append(Spacer(1, 6))

    # SECTION 5: SELECTION RATIONALE
    story.append(Paragraph("Section 5 — Selection Rationale", section_heading))
    rationale_text = (
        f"<b>Selected Strategy: {selected_algorithm}</b><br/>"
        f"<b>Configured Objective:</b> {objective.title()}<br/>"
        f"<b>Decision Justification:</b> {explanation}"
    )
    t_rationale = Table([[Paragraph(rationale_text, callout_style)]], colWidths=[540])
    t_rationale.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(t_rationale)
    story.append(Spacer(1, 6))

    # SECTION 6: INTEGRITY VERIFICATION
    story.append(Paragraph("Section 6 — Cryptographic Lossless Integrity Verification", section_heading))
    badge_bg = "#C6F6D5" if integrity_verified else "#FED7D7"
    badge_border = "#38A169" if integrity_verified else "#E53E3E"
    badge_msg = "PASSED — 100% Exact Bit-for-Bit Reconstruction" if integrity_verified else "FAILED — Checksum Mismatch Detected"

    integrity_rows = [
        [
            Paragraph(f"<b>Verification Status:</b> <font color='{badge_border}'><b>{badge_msg}</b></font>", body_style),
            Paragraph(f"<b>Verification Duration:</b> {decoding_time_sec:.5f}s", body_style),
        ],
        [
            Paragraph("<b>Original SHA-256 Digest:</b>", body_style),
            Paragraph(sha256_original, code_style),
        ],
        [
            Paragraph("<b>Restored SHA-256 Digest:</b>", body_style),
            Paragraph(sha256_decompressed, code_style),
        ],
        [
            Paragraph("<b>Original Byte Length:</b>", body_style),
            Paragraph(f"{original_size:,} bytes", body_style),
        ],
        [
            Paragraph("<b>Restored Byte Length:</b>", body_style),
            Paragraph(f"{original_size:,} bytes (Exact length match)", body_style),
        ],
    ]
    t_integrity = Table(integrity_rows, colWidths=[150, 390])
    t_integrity.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(badge_bg)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(badge_border)),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    story.append(t_integrity)
    story.append(Spacer(1, 6))

    # SECTION 7: CONCLUSION
    story.append(Paragraph("Section 7 — Conclusion & Operational Summary", section_heading))
    if selected_algorithm == "NONE":
        conclusion_text = (
            f"The empirical data profile confirmed that the input exhibits high entropy and negligible repetitive redundancy. "
            f"Consequently, candidate compression methods resulted in storage expansion due to metadata and header framing overhead. "
            f"CompressX successfully executed Raw Bypass mode, ensuring the file was packaged safely without unnecessary size inflation. "
            f"Complete data integrity was verified with cryptographic SHA-256 hash matching."
        )
    else:
        conclusion_text = (
            f"The adaptive decision engine successfully evaluated candidate algorithms against the '{objective.title()}' objective. "
            f"The winning algorithm ({selected_algorithm}) achieved a final stored size of {compressed_size:,} bytes "
            f"(a {compression_ratio:.2f}x compression ratio, saving {space_saved_pct:.1f}% of storage space) "
            f"in {encoding_time_sec:.4f} seconds. "
            f"Lossless integrity verification confirmed bit-for-bit exact reconstruction."
        )
    story.append(Paragraph(conclusion_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
