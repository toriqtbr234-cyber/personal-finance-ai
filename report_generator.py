"""
report_generator.py
───────────────────
Generator laporan PDF FinanceAI menggunakan ReportLab.
Menghasilkan PDF multi-halaman dengan ringkasan keuangan lengkap.
"""

import io
import base64
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Palet warna (sama dengan CSS app) ────────────────────────────────────────
C_BG      = colors.HexColor("#0a0c0f")
C_SURFACE = colors.HexColor("#161b22")
C_CARD    = colors.HexColor("#1c2230")
C_GOLD    = colors.HexColor("#c9a84c")
C_TEAL    = colors.HexColor("#2dd4bf")
C_ROSE    = colors.HexColor("#fb7185")
C_BLUE    = colors.HexColor("#60a5fa")
C_TEXT    = colors.HexColor("#e8eaf0")
C_MUTED   = colors.HexColor("#8b92a5")
C_BORDER  = colors.HexColor("#1c2230")
C_WHITE   = colors.white


# ── Styles ────────────────────────────────────────────────────────────────────
def _build_styles():
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=22,
            textColor=C_TEXT, spaceAfter=4, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=11,
            textColor=C_MUTED, spaceAfter=18, alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "Section", fontName="Helvetica-Bold", fontSize=12,
            textColor=C_GOLD, spaceBefore=18, spaceAfter=8, alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9.5,
            textColor=C_MUTED, spaceAfter=6, leading=14, alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "Label", fontName="Helvetica-Bold", fontSize=8,
            textColor=C_MUTED, spaceAfter=2, alignment=TA_LEFT,
        ),
        "value": ParagraphStyle(
            "Value", fontName="Helvetica-Bold", fontSize=13,
            textColor=C_TEXT, spaceAfter=4, alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "Caption", fontName="Helvetica", fontSize=7.5,
            textColor=C_MUTED, spaceAfter=4, alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=C_MUTED, spaceAfter=6, leading=11, alignment=TA_CENTER,
        ),
    }


def _fmt_rp(angka: float) -> str:
    """Format angka ke string Rupiah yang mudah dibaca."""
    if angka >= 1_000_000_000:
        return f"Rp {angka/1_000_000_000:.2f}M"
    if angka >= 1_000_000:
        return f"Rp {angka/1_000_000:.1f}jt"
    return f"Rp {angka:,.0f}"


def _b64_to_img(b64str: str, width_cm: float = 14) -> Image:
    """Convert base64 PNG string ke ReportLab Image object."""
    data = base64.b64decode(b64str)
    buf  = io.BytesIO(data)
    img  = Image(buf)
    # Maintain aspect ratio
    orig_w, orig_h = img.imageWidth, img.imageHeight
    target_w = width_cm * cm
    img.drawWidth  = target_w
    img.drawHeight = target_w * (orig_h / orig_w)
    return img


def _hr(color=C_BORDER):
    return HRFlowable(width="100%", thickness=1, color=color, spaceAfter=8)


def _stat_table(rows: list, styles_map) -> Table:
    """
    Buat tabel stat 2 kolom: (label, nilai).
    rows: [(label, nilai), ...]
    """
    tbl_data = []
    for label, value in rows:
        tbl_data.append([
            Paragraph(label, styles_map["label"]),
            Paragraph(str(value), styles_map["body"]),
        ])
    tbl = Table(tbl_data, colWidths=[5 * cm, 10 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_SURFACE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_SURFACE, C_CARD]),
        ("TEXTCOLOR", (0, 0), (-1, -1), C_TEXT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


# ════════════════════════════════════════════════════════════════════════════
# FUNGSI UTAMA — generate_pdf_report()
# ════════════════════════════════════════════════════════════════════════════

def generate_pdf_report(
    budget_data:    dict,
    expenses:       list,
    expense_insights: dict,
    savings_plan:   dict,
    invest_guidance: dict,
    charts:         dict,        # { "pie": b64, "bar": b64, "budget": b64, "savings": b64 }
) -> bytes:
    """
    Hasilkan laporan keuangan PDF lengkap.
    Returns: bytes — isi file PDF, siap untuk dikirim sebagai response Flask.
    """
    buf    = io.BytesIO()
    styles = _build_styles()
    now    = datetime.now().strftime("%d %B %Y, %H:%M")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Laporan Keuangan FinanceAI",
        author="FinanceAI",
    )

    story = []

    # ══════════════════════════════════════════════════════════
    # HALAMAN 1 — HEADER & RINGKASAN EKSEKUTIF
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("◈ FinanceAI", styles["title"]))
    story.append(Paragraph(f"Laporan Keuangan Pribadi  ·  Digenerate: {now}", styles["subtitle"]))
    story.append(_hr(C_GOLD))

    # ── Ringkasan 4 angka utama ──────────────────────────────
    b_in   = budget_data.get("input",  {})
    b_out  = budget_data.get("output", {})
    alloc  = b_out.get("alokasi", {})
    total_expense = sum(float(e.get("jumlah", 0)) for e in expenses)

    pendapatan       = float(b_in.get("pendapatan", 0))
    pengeluaran_plan = float(b_in.get("pengeluaran_wajib", 0)) + float(b_in.get("pengeluaran_tambahan", 0))
    tabungan_plan    = float(alloc.get("tabungan", 0))
    status           = b_out.get("status", "—").capitalize()

    summary_data = [
        ["Pendapatan Bulanan",    "Total Pengeluaran Aktual"],
        [_fmt_rp(pendapatan) if pendapatan else "—",
         _fmt_rp(total_expense) if total_expense else "—"],
        ["Alokasi Tabungan (AI)", "Status Keuangan"],
        [_fmt_rp(tabungan_plan) if tabungan_plan else "—", status],
    ]

    tbl_summary = Table(summary_data, colWidths=[8.25 * cm, 8.25 * cm])
    tbl_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_SURFACE),
        ("BACKGROUND", (0, 0), (1, 0), C_CARD),
        ("BACKGROUND", (0, 2), (1, 2), C_CARD),
        ("TEXTCOLOR", (0, 0), (-1, -1), C_MUTED),
        ("TEXTCOLOR", (0, 1), (-1, 1), C_TEAL),
        ("TEXTCOLOR", (0, 3), (-1, 3), C_GOLD),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTSIZE", (0, 1), (-1, 1), 17),
        ("FONTSIZE", (0, 3), (-1, 3), 17),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl_summary)
    story.append(Spacer(1, 16))

    # ── Saran AI dari budget planner ───────────────────────────
    if b_out.get("saran_ai"):
        story.append(Paragraph("Analisis AI", styles["section"]))
        story.append(Paragraph(b_out["saran_ai"], styles["body"]))
        if b_out.get("ringkasan"):
            story.append(Paragraph(f"<i>{b_out['ringkasan']}</i>", styles["body"]))
        story.append(Spacer(1, 6))

    # ── Grafik overview (jika tersedia) ────────────────────────
    if charts.get("overview"):
        story.append(Paragraph("Ringkasan Visual", styles["section"]))
        story.append(_b64_to_img(charts["overview"], width_cm=16))
        story.append(Paragraph("Gambar 1 — Dashboard Grafik Keuangan", styles["caption"]))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # HALAMAN 2 — BUDGET PLANNER DETAIL
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Budget Planner", styles["section"]))
    story.append(_hr())

    if b_in:
        rows_budget = [
            ("Pendapatan Bulanan",        _fmt_rp(float(b_in.get("pendapatan", 0)))),
            ("Pengeluaran Wajib",          _fmt_rp(float(b_in.get("pengeluaran_wajib", 0)))),
            ("Pengeluaran Sehari-hari",    _fmt_rp(float(b_in.get("pengeluaran_tambahan", 0)))),
            ("Kota",                       b_in.get("kota", "—")),
            ("Jumlah Tanggungan",          str(b_in.get("tanggungan", 0)) + " orang"),
        ]
        story.append(_stat_table(rows_budget, styles))
        story.append(Spacer(1, 12))

    if alloc:
        story.append(Paragraph("Alokasi Anggaran yang Disarankan AI", styles["label"]))
        alloc_data = [
            ["Kategori", "Jumlah (Rp)", "Persentase"],
            ["Kebutuhan", _fmt_rp(float(alloc.get("kebutuhan", 0))),
             str(b_out.get("persen", {}).get("kebutuhan", "—")) + "%"],
            ["Keinginan",  _fmt_rp(float(alloc.get("keinginan", 0))),
             str(b_out.get("persen", {}).get("keinginan", "—")) + "%"],
            ["Tabungan",   _fmt_rp(float(alloc.get("tabungan",  0))),
             str(b_out.get("persen", {}).get("tabungan",  "—")) + "%"],
        ]
        tbl_alloc = Table(alloc_data, colWidths=[6 * cm, 6 * cm, 4.5 * cm])
        tbl_alloc.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),  C_CARD),
            ("BACKGROUND", (0, 1), (-1, 1),  colors.HexColor("#0d2244")),
            ("BACKGROUND", (0, 2), (-1, 2),  C_SURFACE),
            ("BACKGROUND", (0, 3), (-1, 3),  colors.HexColor("#0d2a25")),
            ("TEXTCOLOR",  (0, 0), (-1, 0),  C_GOLD),
            ("TEXTCOLOR",  (0, 1), (-1, -1), C_TEXT),
            ("FONTNAME",   (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        story.append(tbl_alloc)
        story.append(Spacer(1, 10))

    if charts.get("budget"):
        story.append(_b64_to_img(charts["budget"], width_cm=10))
        story.append(Paragraph("Gambar 2 — Distribusi Alokasi Anggaran", styles["caption"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # HALAMAN 3 — EXPENSE ANALYZER
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Expense Analyzer", styles["section"]))
    story.append(_hr())

    if expenses:
        story.append(Paragraph(
            f"Total {len(expenses)} transaksi  ·  Total pengeluaran: {_fmt_rp(total_expense)}",
            styles["body"]
        ))
        story.append(Spacer(1, 8))

        # Tabel ringkasan per kategori
        totals_kat = {}
        for e in expenses:
            k = e.get("kategori", "Lainnya")
            totals_kat[k] = totals_kat.get(k, 0) + float(e.get("jumlah", 0))

        kat_data = [["Kategori", "Total (Rp)", "% dari Total"]]
        for k, v in sorted(totals_kat.items(), key=lambda x: -x[1]):
            pct = v / total_expense * 100 if total_expense else 0
            kat_data.append([k, _fmt_rp(v), f"{pct:.1f}%"])

        tbl_kat = Table(kat_data, colWidths=[7 * cm, 5.5 * cm, 4 * cm])
        tbl_kat.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),  C_CARD),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_SURFACE, C_BG]),
            ("TEXTCOLOR",  (0, 0), (-1, 0),  C_GOLD),
            ("TEXTCOLOR",  (0, 1), (-1, -1), C_TEXT),
            ("FONTNAME",   (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))
        story.append(tbl_kat)
        story.append(Spacer(1, 10))

    if charts.get("pie"):
        story.append(_b64_to_img(charts["pie"], width_cm=10))
        story.append(Paragraph("Gambar 3 — Distribusi Pengeluaran per Kategori", styles["caption"]))

    if expense_insights:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Insight AI", styles["label"]))
        story.append(Paragraph(expense_insights.get("insight_utama", ""), styles["body"]))

        if expense_insights.get("area_boros"):
            story.append(Paragraph("Area Pengeluaran Berlebihan:", styles["label"]))
            for ab in expense_insights["area_boros"]:
                story.append(Paragraph(
                    f"<b>{ab['kategori']}</b>: {ab['alasan']}", styles["body"]
                ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # HALAMAN 4 — SAVINGS & INVESTMENT
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Savings Goal Planner", styles["section"]))
    story.append(_hr())

    if savings_plan:
        rows_sv = [
            ("Nama Tujuan",       savings_plan.get("nama_tujuan", "—")),
            ("Target Dana",       _fmt_rp(float(savings_plan.get("target_jumlah", 0)))),
            ("Dana Awal",         _fmt_rp(float(savings_plan.get("tabungan_awal",  0)))),
            ("Durasi",            f"{savings_plan.get('durasi_bulan', '—')} bulan"),
            ("Tabungan/Bulan",    _fmt_rp(float(savings_plan.get("tabungan_per_bulan", 0)))),
            ("Total Ditabung",    _fmt_rp(float(savings_plan.get("total_ditabung", 0)))),
            ("Est. Bunga (4%/thn)", _fmt_rp(float(savings_plan.get("bunga_estimasi", 0)))),
            ("Total + Bunga",     _fmt_rp(float(savings_plan.get("total_dengan_bunga", 0)))),
            ("Kelayakan",         savings_plan.get("feasibility", "—").capitalize()),
        ]
        story.append(_stat_table(rows_sv, styles))
        story.append(Spacer(1, 10))

        if savings_plan.get("strategi_utama"):
            story.append(Paragraph(savings_plan["strategi_utama"], styles["body"]))
        if savings_plan.get("catatan_ai"):
            story.append(Paragraph(f"<i>{savings_plan['catatan_ai']}</i>", styles["body"]))

        if charts.get("savings"):
            story.append(Spacer(1, 8))
            story.append(_b64_to_img(charts["savings"], width_cm=14))
            story.append(Paragraph("Gambar 4 — Proyeksi Akumulasi Tabungan", styles["caption"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Investment Guidance", styles["section"]))
    story.append(_hr())

    if invest_guidance:
        story.append(Paragraph(
            f"Profil Risiko: <b>{invest_guidance.get('profil', '—')}</b>  ·  "
            f"Horizon: {invest_guidance.get('waktu_ideal', '—')}",
            styles["body"]
        ))
        if invest_guidance.get("deskripsi_profil"):
            story.append(Paragraph(invest_guidance["deskripsi_profil"], styles["body"]))
        if invest_guidance.get("strategi_masuk"):
            story.append(Paragraph(invest_guidance["strategi_masuk"], styles["body"]))

    # ══════════════════════════════════════════════════════════
    # FOOTER — Disclaimer
    # ══════════════════════════════════════════════════════════
    story.append(Spacer(1, 30))
    story.append(_hr(C_MUTED))
    story.append(Paragraph(
        "Laporan ini digenerate oleh FinanceAI dan bersifat informatif/edukatif. "
        "FinanceAI bukan penasihat keuangan atau investasi berlisensi. "
        "Semua keputusan keuangan sepenuhnya merupakan tanggung jawab pengguna.",
        styles["disclaimer"]
    ))
    story.append(Paragraph(f"FinanceAI  ·  {now}", styles["disclaimer"]))

    doc.build(story)
    buf.seek(0)
    return buf.read()
