"""
chart_generator.py
──────────────────
Semua fungsi visualisasi Matplotlib untuk FinanceAI.
Setiap fungsi mengembalikan string base64 PNG agar bisa langsung
di-embed di HTML (<img src="data:image/png;base64,...">)
dan juga bisa dipakai oleh ReportLab untuk PDF.
"""

import io
import base64
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend (wajib untuk Flask)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec


# ── Tema warna konsisten dengan CSS app ──────────────────────────────────────
PALETTE = {
    "bg":       "#0a0c0f",
    "surface":  "#161b22",
    "border":   "#1c2230",
    "gold":     "#c9a84c",
    "teal":     "#2dd4bf",
    "rose":     "#fb7185",
    "blue":     "#60a5fa",
    "text":     "#e8eaf0",
    "muted":    "#4a5068",
}

# Warna per kategori pengeluaran (harus konsisten dengan JS di expenses.html)
CAT_COLORS = {
    "Makanan & Minuman":    "#60a5fa",
    "Transportasi":         "#f59e0b",
    "Belanja & Pakaian":    "#a78bfa",
    "Kesehatan":            "#34d399",
    "Hiburan & Rekreasi":   "#f472b6",
    "Pendidikan":           "#38bdf8",
    "Tagihan & Utilitas":   "#fb923c",
    "Tabungan & Investasi": "#2dd4bf",
    "Sosial & Hadiah":      "#e879f9",
    "Lainnya":              "#94a3b8",
}


def _fig_to_b64(fig) -> str:
    """Convert Matplotlib figure ke base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def _apply_dark_theme(ax, title="", xlabel="", ylabel=""):
    """Terapkan tema gelap konsisten ke semua axes."""
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["muted"], labelsize=8)
    ax.spines[:].set_color(PALETTE["border"])
    if title:
        ax.set_title(title, color=PALETTE["text"], fontsize=11,
                     fontweight="bold", pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, color=PALETTE["muted"], fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=PALETTE["muted"], fontsize=9)


# ════════════════════════════════════════════════════════════════════════════
# 1. Pie Chart — Distribusi Pengeluaran per Kategori
# ════════════════════════════════════════════════════════════════════════════

def chart_expense_pie(expenses: list) -> str:
    """
    Pie chart pengeluaran per kategori.
    Returns: base64 PNG string
    """
    if not expenses:
        return ""

    # Hitung per kategori
    totals = {}
    for e in expenses:
        kat = e.get("kategori", "Lainnya")
        totals[kat] = totals.get(kat, 0) + float(e.get("jumlah", 0))

    if not totals:
        return ""

    # Urutkan terbesar ke terkecil
    sorted_items = sorted(totals.items(), key=lambda x: -x[1])
    labels = [k for k, _ in sorted_items]
    sizes  = [v for _, v in sorted_items]
    colors = [CAT_COLORS.get(k, "#94a3b8") for k in labels]

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        colors=colors,
        autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
        startangle=140,
        wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 2},
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_color(PALETTE["bg"])
        at.set_fontsize(8)
        at.set_fontweight("bold")

    # Donut effect
    circle = plt.Circle((0, 0), 0.55, color=PALETTE["bg"])
    ax.add_patch(circle)

    # Teks tengah
    total = sum(sizes)
    ax.text(0, 0.08, "Total", ha="center", va="center",
            color=PALETTE["muted"], fontsize=8)
    ax.text(0, -0.12, f"Rp {total:,.0f}", ha="center", va="center",
            color=PALETTE["text"], fontsize=9, fontweight="bold")

    # Legend
    legend_patches = [
        mpatches.Patch(color=colors[i], label=f"{labels[i]}")
        for i in range(len(labels))
    ]
    ax.legend(
        handles=legend_patches,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=7.5,
        frameon=False,
        labelcolor=PALETTE["text"],
    )
    ax.set_title("Distribusi Pengeluaran per Kategori",
                 color=PALETTE["text"], fontsize=11, fontweight="bold", pad=14)

    fig.tight_layout()
    return _fig_to_b64(fig)


# ════════════════════════════════════════════════════════════════════════════
# 2. Bar Chart — Pengeluaran per Kategori
# ════════════════════════════════════════════════════════════════════════════

def chart_expense_bar(expenses: list) -> str:
    """
    Horizontal bar chart pengeluaran per kategori, diurutkan terbesar.
    Returns: base64 PNG string
    """
    if not expenses:
        return ""

    totals = {}
    for e in expenses:
        kat = e.get("kategori", "Lainnya")
        totals[kat] = totals.get(kat, 0) + float(e.get("jumlah", 0))

    if not totals:
        return ""

    sorted_items = sorted(totals.items(), key=lambda x: x[1])   # ascending untuk hbar
    labels = [k for k, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors = [CAT_COLORS.get(k, "#94a3b8") for k in labels]

    fig, ax = plt.subplots(figsize=(6.5, max(3.5, len(labels) * 0.48)))
    fig.patch.set_facecolor(PALETTE["bg"])
    _apply_dark_theme(ax, title="Pengeluaran per Kategori (Rp)")

    bars = ax.barh(labels, values, color=colors,
                   edgecolor=PALETTE["bg"], linewidth=0.8, height=0.6)

    # Label nilai di ujung bar
    max_val = max(values)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + max_val * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"Rp {val:,.0f}",
            va="center", ha="left",
            color=PALETTE["muted"], fontsize=7.5,
        )

    ax.set_xlim(0, max_val * 1.32)
    ax.tick_params(axis="y", labelsize=8.5, colors=PALETTE["text"])
    ax.tick_params(axis="x", labelsize=7.5)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"Rp {x/1e6:.1f}jt" if x >= 1e6 else f"Rp {x/1e3:.0f}rb")
    )
    ax.grid(axis="x", color=PALETTE["border"], linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return _fig_to_b64(fig)


# ════════════════════════════════════════════════════════════════════════════
# 3. Donut Chart — Distribusi Alokasi Anggaran (50/30/20)
# ════════════════════════════════════════════════════════════════════════════

def chart_budget_donut(budget_data: dict) -> str:
    """
    Donut chart alokasi anggaran dari hasil budget planner AI.
    Returns: base64 PNG string
    """
    alloc = budget_data.get("output", {}).get("alokasi", {})
    pct   = budget_data.get("output", {}).get("persen", {})

    if not alloc or not any(alloc.values()):
        return ""

    labels = ["Kebutuhan", "Keinginan", "Tabungan"]
    values = [
        float(alloc.get("kebutuhan", 0)),
        float(alloc.get("keinginan", 0)),
        float(alloc.get("tabungan",  0)),
    ]
    colors = [PALETTE["blue"], PALETTE["gold"], PALETTE["teal"]]

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    wedges, _, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        autopct=lambda p: f"{p:.0f}%",
        startangle=90,
        wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 3},
        pctdistance=0.78,
    )
    for at in autotexts:
        at.set_color(PALETTE["bg"])
        at.set_fontsize(9)
        at.set_fontweight("bold")

    # Donut hole
    circle = plt.Circle((0, 0), 0.55, color=PALETTE["bg"])
    ax.add_patch(circle)

    # Label tengah
    pendapatan = budget_data.get("input", {}).get("pendapatan", 0)
    ax.text(0, 0.1, "Pendapatan", ha="center", color=PALETTE["muted"], fontsize=8)
    ax.text(0, -0.12, f"Rp {pendapatan:,.0f}" if pendapatan else "—",
            ha="center", color=PALETTE["text"], fontsize=8.5, fontweight="bold")

    legend_patches = [
        mpatches.Patch(color=colors[i], label=f"{labels[i]}: Rp {values[i]:,.0f} ({pct.get(labels[i].lower(), '—')}%)")
        for i in range(3)
    ]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.1), ncol=1,
              fontsize=8, frameon=False, labelcolor=PALETTE["text"])
    ax.set_title("Distribusi Alokasi Anggaran",
                 color=PALETTE["text"], fontsize=11, fontweight="bold", pad=14)

    fig.tight_layout()
    return _fig_to_b64(fig)


# ════════════════════════════════════════════════════════════════════════════
# 4. Bar Chart — Perbandingan Anggaran vs Realisasi Pengeluaran
# ════════════════════════════════════════════════════════════════════════════

def chart_budget_vs_actual(budget_data: dict, total_expense: float) -> str:
    """
    Grouped bar: anggaran yang direncanakan vs pengeluaran aktual.
    Returns: base64 PNG string
    """
    alloc = budget_data.get("output", {}).get("alokasi", {})
    inp   = budget_data.get("input", {})

    if not alloc or not inp.get("pendapatan"):
        return ""

    pendapatan       = float(inp.get("pendapatan", 0))
    pengeluaran_wajib = float(inp.get("pengeluaran_wajib", 0))
    pengeluaran_harian = float(inp.get("pengeluaran_tambahan", 0))
    total_planned    = pengeluaran_wajib + pengeluaran_harian

    categories  = ["Pengeluaran\nDianggarkan", "Pengeluaran\nAktual", "Alokasi\nTabungan"]
    planned_val = [total_planned, total_planned, float(alloc.get("tabungan", 0))]
    actual_val  = [total_expense, total_expense, pendapatan - total_expense]

    import numpy as np
    x      = np.arange(len(categories))
    width  = 0.32

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    fig.patch.set_facecolor(PALETTE["bg"])
    _apply_dark_theme(ax, title="Anggaran yang Direncanakan vs Aktual")

    b1 = ax.bar(x - width/2, planned_val, width,
                label="Direncanakan", color=PALETTE["blue"], alpha=0.85)
    b2 = ax.bar(x + width/2, actual_val,  width,
                label="Aktual",       color=PALETTE["gold"], alpha=0.85)

    def add_labels(bars):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + max(planned_val + actual_val) * 0.01,
                    f"Rp {h/1e6:.1f}jt" if h >= 1e6 else f"Rp {h/1e3:.0f}rb",
                    ha="center", va="bottom", color=PALETTE["muted"], fontsize=7.5)

    add_labels(b1)
    add_labels(b2)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, color=PALETTE["text"], fontsize=8.5)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda y, _: f"Rp {y/1e6:.1f}jt" if y >= 1e6 else f"Rp {y/1e3:.0f}rb")
    )
    ax.legend(fontsize=8.5, frameon=False, labelcolor=PALETTE["text"])
    ax.grid(axis="y", color=PALETTE["border"], linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return _fig_to_b64(fig)


# ════════════════════════════════════════════════════════════════════════════
# 5. Line Chart — Proyeksi Tabungan (Savings Goal)
# ════════════════════════════════════════════════════════════════════════════

def chart_savings_projection(savings_plan: dict) -> str:
    """
    Line chart proyeksi akumulasi tabungan bulan per bulan.
    Returns: base64 PNG string
    """
    if not savings_plan or not savings_plan.get("tabungan_per_bulan"):
        return ""

    bulanan  = float(savings_plan.get("tabungan_per_bulan", 0))
    awal     = float(savings_plan.get("tabungan_awal", 0))
    durasi   = int(savings_plan.get("durasi_bulan", 12))
    target   = float(savings_plan.get("target_jumlah", 0))
    nama     = savings_plan.get("nama_tujuan", "Tujuan")

    # Proyeksi tanpa bunga
    months  = list(range(0, durasi + 1))
    tanpa_b = [awal + bulanan * m for m in months]

    # Proyeksi dengan bunga compound 4%/thn
    r       = 0.04 / 12
    dengan_b = [awal]
    total = awal
    for _ in range(durasi):
        total = total * (1 + r) + bulanan
        dengan_b.append(total)

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor(PALETTE["bg"])
    _apply_dark_theme(ax, title=f"Proyeksi Tabungan: {nama}",
                      xlabel="Bulan ke-", ylabel="Akumulasi (Rp)")

    ax.plot(months, tanpa_b,   color=PALETTE["blue"],  linewidth=2,
            label="Tanpa bunga", linestyle="--")
    ax.plot(months, dengan_b,  color=PALETTE["teal"],  linewidth=2.5,
            label="Dengan bunga 4%/thn")
    ax.fill_between(months, tanpa_b, dengan_b,
                    color=PALETTE["teal"], alpha=0.08)

    if target > 0:
        ax.axhline(target, color=PALETTE["gold"], linewidth=1.5,
                   linestyle=":", label=f"Target: Rp {target:,.0f}")

    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda y, _: f"Rp {y/1e6:.1f}jt" if y >= 1e6 else f"Rp {y/1e3:.0f}rb")
    )
    ax.legend(fontsize=8, frameon=False, labelcolor=PALETTE["text"])
    ax.grid(color=PALETTE["border"], linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return _fig_to_b64(fig)


# ════════════════════════════════════════════════════════════════════════════
# 6. Dashboard Overview (2x2 grid) — untuk laporan PDF
# ════════════════════════════════════════════════════════════════════════════

def chart_dashboard_overview(expenses: list, budget_data: dict,
                              total_expense: float, savings_plan: dict) -> str:
    """
    Gabungan 4 grafik dalam satu figure (untuk preview & PDF).
    Returns: base64 PNG string
    """
    fig = plt.figure(figsize=(13, 9))
    fig.patch.set_facecolor(PALETTE["bg"])
    gs = GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.38)

    # ── Panel 1: Pie pengeluaran ──────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    if expenses:
        totals = {}
        for e in expenses:
            kat = e.get("kategori", "Lainnya")
            totals[kat] = totals.get(kat, 0) + float(e.get("jumlah", 0))
        sorted_items = sorted(totals.items(), key=lambda x: -x[1])
        labels_p = [k for k, _ in sorted_items][:8]
        sizes_p  = [v for _, v in sorted_items][:8]
        colors_p = [CAT_COLORS.get(k, "#94a3b8") for k in labels_p]
        ax1.pie(sizes_p, colors=colors_p, startangle=140,
                wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 1.5},
                autopct=lambda p: f"{p:.0f}%" if p > 6 else "",
                pctdistance=0.82)
        circle1 = plt.Circle((0, 0), 0.55, color=PALETTE["bg"])
        ax1.add_patch(circle1)
    _apply_dark_theme(ax1, title="Distribusi Pengeluaran")
    ax1.set_facecolor(PALETTE["bg"])

    # ── Panel 2: Budget donut ──────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    alloc = budget_data.get("output", {}).get("alokasi", {})
    if alloc and any(alloc.values()):
        vals2   = [float(alloc.get(k, 0)) for k in ["kebutuhan", "keinginan", "tabungan"]]
        colors2 = [PALETTE["blue"], PALETTE["gold"], PALETTE["teal"]]
        ax2.pie(vals2, colors=colors2, startangle=90,
                wedgeprops={"edgecolor": PALETTE["bg"], "linewidth": 1.5},
                autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
                pctdistance=0.78)
        circle2 = plt.Circle((0, 0), 0.55, color=PALETTE["bg"])
        ax2.add_patch(circle2)
    _apply_dark_theme(ax2, title="Alokasi Anggaran")
    ax2.set_facecolor(PALETTE["bg"])

    # ── Panel 3: Bar pengeluaran ───────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    if expenses:
        sorted_items3 = sorted(totals.items(), key=lambda x: x[1])[-8:]
        labs3  = [k for k, _ in sorted_items3]
        vals3  = [v for _, v in sorted_items3]
        cols3  = [CAT_COLORS.get(k, "#94a3b8") for k in labs3]
        ax3.barh(labs3, vals3, color=cols3, edgecolor=PALETTE["bg"], height=0.6)
        ax3.set_facecolor(PALETTE["surface"])
        ax3.tick_params(axis="y", labelsize=7, colors=PALETTE["text"])
        ax3.tick_params(axis="x", labelsize=6.5, colors=PALETTE["muted"])
        ax3.spines[:].set_color(PALETTE["border"])
        ax3.xaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1e6:.1f}jt" if x >= 1e6 else f"{x/1e3:.0f}rb")
        )
        ax3.grid(axis="x", color=PALETTE["border"], linestyle="--", alpha=0.4)
        ax3.set_axisbelow(True)
    _apply_dark_theme(ax3, title="Pengeluaran per Kategori")

    # ── Panel 4: Savings projection ───────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    if savings_plan and savings_plan.get("tabungan_per_bulan"):
        bulanan4 = float(savings_plan.get("tabungan_per_bulan", 0))
        awal4    = float(savings_plan.get("tabungan_awal", 0))
        dur4     = int(savings_plan.get("durasi_bulan", 12))
        target4  = float(savings_plan.get("target_jumlah", 0))
        months4  = list(range(dur4 + 1))
        proj4    = [awal4 + bulanan4 * m for m in months4]
        r = 0.04 / 12
        proj_b4, tot4 = [awal4], awal4
        for _ in range(dur4):
            tot4 = tot4 * (1 + r) + bulanan4
            proj_b4.append(tot4)
        ax4.plot(months4, proj4,   color=PALETTE["blue"], linewidth=1.5, linestyle="--")
        ax4.plot(months4, proj_b4, color=PALETTE["teal"], linewidth=2)
        if target4:
            ax4.axhline(target4, color=PALETTE["gold"], linewidth=1.2, linestyle=":")
        ax4.set_facecolor(PALETTE["surface"])
        ax4.tick_params(colors=PALETTE["muted"], labelsize=7)
        ax4.spines[:].set_color(PALETTE["border"])
        ax4.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda y, _: f"{y/1e6:.1f}jt" if y >= 1e6 else f"{y/1e3:.0f}rb")
        )
        ax4.grid(color=PALETTE["border"], linestyle="--", alpha=0.3)
    _apply_dark_theme(ax4, title="Proyeksi Tabungan")

    return _fig_to_b64(fig)
