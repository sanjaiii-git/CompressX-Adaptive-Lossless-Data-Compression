"""PDF Technical Report Generator for CompressX (Adaptive Hybrid Data Compression).

Generates a publication-grade, professional technical report including:
- Document header & metadata summary
- Information-theoretic empirical metrics (Entropy, Repetition, Gini Skew)
- Decision engine explainability breakdown
- Comprehensive compression performance metrics & comparison
- Cryptographic SHA-256 integrity verification badge
- Embedded vector/raster performance visualization chart
- Official audit footer
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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _generate_comparison_chart(
    original_size: int, compressed_size: int, comparison_rows: Optional[List[Dict[str, Any]]] = None
) -> io.BytesIO:
    """Generate a clean matplotlib comparison bar chart in-memory."""
    plt.figure(figsize=(7, 2.6))
    
    if comparison_rows and len(comparison_rows) > 0:
        names = [r["Algorithm"].replace(" (Baseline)", "").replace("Hybrid (RLE+Huffman)", "Hybrid") for r in comparison_rows]
        sizes = [r["Compressed Size (B)"] for r in comparison_rows]
        # Include original size as reference
        all_names = ["Original"] + names
        all_sizes = [original_size] + sizes
        colors_list = ["#4A5568"] + ["#2B6CB0" if "Adaptive" in n else "#4299E1" for n in names]
        
        y_pos = range(len(all_names))
        bars = plt.barh(y_pos, all_sizes, color=colors_list, edgecolor="#2D3748", height=0.6)
        plt.yticks(y_pos, all_names, fontsize=8, fontweight="bold")
        plt.xlabel("Size (Bytes)", fontsize=8)
        plt.title("Size Comparison Across Compression Methods", fontsize=9, fontweight="bold", pad=8)
        
        # Add data labels
        for bar in bars:
            w = bar.get_width()
            plt.text(w + (max(all_sizes) * 0.01), bar.get_y() + bar.get_height()/2, f"{int(w):,} B", 
                     va="center", fontsize=7, color="#2D3748")
        
        plt.xlim(0, max(all_sizes) * 1.18)
    else:
        labels = ["Original File", "CompressX (.ahdc)"]
        sizes = [original_size, compressed_size]
        bar_colors = ["#4A5568", "#2B6CB0"]
        bars = plt.barh([0, 1], sizes, color=bar_colors, edgecolor="#2D3748", height=0.45)
        plt.yticks([0, 1], labels, fontsize=8, fontweight="bold")
        plt.xlabel("Size (Bytes)", fontsize=8)
        plt.title("Before vs. After Compression", fontsize=9, fontweight="bold", pad=8)
        for bar in bars:
            w = bar.get_width()
            plt.text(w + (max(sizes) * 0.02), bar.get_y() + bar.get_height()/2, f"{int(w):,} B", 
                     va="center", fontsize=7)
        plt.xlim(0, max(sizes) * 1.2)

    plt.gca().invert_yaxis()
    plt.grid(axis="x", linestyle="--", alpha=0.5)
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
    comparison_rows: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """Generate a complete technical PDF report and return raw PDF bytes."""
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

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=10,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
    )
    callout_style = ParagraphStyle(
        "DocCallout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1A202C"),
    )
    code_style = ParagraphStyle(
        "DocCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#2C5282"),
    )

    story = []

    # 1. HEADER BANNER
    story.append(Paragraph("COMPRESSX — ADAPTIVE DATA COMPRESSION TOOL", title_style))
    story.append(
        Paragraph(
            f"Technical Compression & Lossless Verification Report • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    # 2. FILE & JOB SUMMARY TABLE
    story.append(Paragraph("1. File & Compression Job Overview", section_heading))
    overview_data = [
        [
            Paragraph("<b>Target File Name:</b>", body_style),
            Paragraph(file_name, body_style),
            Paragraph("<b>Selected Algorithm:</b>", body_style),
            Paragraph(f"<b>{selected_algorithm}</b>", body_style),
        ],
        [
            Paragraph("<b>Original Size:</b>", body_style),
            Paragraph(f"{original_size:,} bytes ({original_size / 1024:.2f} KB)", body_style),
            Paragraph("<b>Compressed Size:</b>", body_style),
            Paragraph(f"{compressed_size:,} bytes ({compressed_size / 1024:.2f} KB)", body_style),
        ],
        [
            Paragraph("<b>Compression Ratio:</b>", body_style),
            Paragraph(f"<b>{compression_ratio:.3f}x</b>", body_style),
            Paragraph("<b>Space Reduction:</b>", body_style),
            Paragraph(f"<b>{space_saved_pct:.2f}%</b>", body_style),
        ],
        [
            Paragraph("<b>Encoding Latency:</b>", body_style),
            Paragraph(f"{encoding_time_sec:.5f} sec", body_style),
            Paragraph("<b>Decoding Latency:</b>", body_style),
            Paragraph(f"{decoding_time_sec:.5f} sec", body_style),
        ],
    ]
    t_overview = Table(overview_data, colWidths=[110, 160, 110, 160])
    t_overview.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t_overview)
    story.append(Spacer(1, 8))

    # 3. STATISTICAL & EMPIRICAL PROFILING
    story.append(Paragraph("2. Information-Theoretic & Statistical Profiling", section_heading))
    ent = profile.get("entropy", 0.0)
    rep_pct = profile.get("repetition_percentage", 0.0)
    avg_run = profile.get("average_run_length", 0.0)
    uniq = profile.get("unique_symbols", 0)
    gini = profile.get("gini_coefficient", 0.0)

    analysis_data = [
        [
            Paragraph("<b>Metric</b>", body_style),
            Paragraph("<b>Value</b>", body_style),
            Paragraph("<b>Theoretical Significance / Decision Impact</b>", body_style),
        ],
        [
            Paragraph("Shannon Entropy H(X)", body_style),
            Paragraph(f"<b>{ent:.4f}</b> bits/sym", body_style),
            Paragraph("Fundamental compressibility lower bound (max 8.0 bits for byte streams).", body_style),
        ],
        [
            Paragraph("Repetition Percentage", body_style),
            Paragraph(f"<b>{rep_pct:.2f}%</b>", body_style),
            Paragraph("Fraction of symbols forming runs of length >= 2.", body_style),
        ],
        [
            Paragraph("Average Run Length", body_style),
            Paragraph(f"<b>{avg_run:.2f}</b>", body_style),
            Paragraph("Values > 2.0 satisfy the mathematical profitability threshold for RLE.", body_style),
        ],
        [
            Paragraph("Alphabet Cardinality", body_style),
            Paragraph(f"<b>{uniq}</b> / 256", body_style),
            Paragraph("Number of unique 8-bit symbols observed in the input stream.", body_style),
        ],
        [
            Paragraph("Frequency Skew (Gini)", body_style),
            Paragraph(f"<b>{gini:.4f}</b>", body_style),
            Paragraph("Gini coefficient of symbol frequencies (higher = more uneven = ideal for Huffman).", body_style),
        ],
    ]
    t_analysis = Table(analysis_data, colWidths=[140, 90, 310])
    t_analysis.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ])
    )
    story.append(t_analysis)
    story.append(Spacer(1, 8))

    # 4. DECISION ENGINE EXPLANATION
    story.append(Paragraph("3. Intelligent Strategy Selection Rationale", section_heading))
    rationale_p = Paragraph(f"<b>Selected Strategy: {selected_algorithm}</b><br/>{explanation}", callout_style)
    t_rationale = Table([[rationale_p]], colWidths=[540])
    t_rationale.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(t_rationale)
    story.append(Spacer(1, 8))

    # 5. INTEGRITY VERIFICATION
    story.append(Paragraph("4. Cryptographic Lossless Integrity Verification", section_heading))
    badge_color = "#C6F6D5" if integrity_verified else "#FED7D7"
    border_color = "#38A169" if integrity_verified else "#E53E3E"
    status_text = "PASSED (Exact Bit-for-Bit Reconstruction)" if integrity_verified else "FAILED (Checksum Mismatch)"

    integrity_content = [
        Paragraph(f"<b>Status: {status_text}</b>", callout_style),
        Spacer(1, 2),
        Paragraph(f"<b>Original SHA-256:</b> {sha256_original}", code_style),
        Paragraph(f"<b>Restored SHA-256:</b> {sha256_decompressed}", code_style),
    ]
    t_integrity = Table([[integrity_content]], colWidths=[540])
    t_integrity.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(badge_color)),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(border_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(t_integrity)
    story.append(Spacer(1, 8))

    # 6. VISUAL PERFORMANCE CHART
    story.append(Paragraph("5. Visual Compression Performance", section_heading))
    chart_buf = _generate_comparison_chart(original_size, compressed_size, comparison_rows)
    story.append(Image(chart_buf, width=7.2 * inch, height=2.4 * inch))
    story.append(Spacer(1, 10))

    # 7. FOOTER
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=4))
    footer_text = Paragraph(
        "<b>CompressX v2.0</b> • Academic Lossless Data Compression System • "
        "Verified Lossless Execution Pipeline • Container Specification: AHDC-v1",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#718096"), alignment=1),
    )
    story.append(footer_text)

    # Build document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
