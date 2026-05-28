from flask import Flask, render_template, session, request, jsonify, send_file
from config import Config
from gemini_client import (
    generate_budget_advice,
    generate_expense_insights,
    chat_financial_advisor,
    generate_savings_plan,
    generate_investment_guidance,
    EXPENSE_CATEGORIES,
    QUICK_TOPICS,
    PROFIL_RISIKO,
)
from chart_generator import (
    chart_expense_pie,
    chart_expense_bar,
    chart_budget_donut,
    chart_budget_vs_actual,
    chart_savings_projection,
    chart_dashboard_overview,
)
from report_generator import generate_pdf_report
import csv, io

app = Flask(__name__)
app.config.from_object(Config)


# ─── Helper: pastikan session storage tersedia ────────────────────────────────
def init_session():
    """Inisialisasi struktur data in-memory di session jika belum ada."""
    if "expenses" not in session:
        session["expenses"] = []
    if "expense_insights" not in session:
        session["expense_insights"] = {}
    if "budget" not in session:
        session["budget"] = {}
    if "savings_goals" not in session:
        session["savings_goals"] = []
    if "savings_plan" not in session:
        session["savings_plan"] = {}
    if "invest_guidance" not in session:
        session["invest_guidance"] = {}
    if "chat_history" not in session:
        session["chat_history"] = []


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    """Halaman utama: Dashboard ringkasan keuangan."""
    init_session()
    budget_data   = session.get("budget", {})
    expenses_data = session.get("expenses", [])
    insights_data = session.get("expense_insights", {})

    # Hitung total pengeluaran untuk dashboard
    total_expense = sum(float(e.get("jumlah", 0)) for e in expenses_data)

    return render_template(
        "index.html",
        page="dashboard",
        budget=budget_data,
        total_expense=total_expense,
        expense_count=len(expenses_data),
        insights=insights_data
    )


# ── Budget Planner ─────────────────────────────────────────────────────────────

@app.route("/budget", methods=["GET"])
def budget():
    """Halaman Budget Planner – Week 2 (GET: tampilkan form)."""
    init_session()
    budget_data = session.get("budget", {})
    return render_template("budget.html", page="budget", budget=budget_data)


@app.route("/budget/analyze", methods=["POST"])
def budget_analyze():
    """
    API endpoint – Week 2 (POST: terima data form, panggil Gemini, kembalikan JSON).
    Dipanggil oleh JavaScript di budget.html via fetch().
    """
    init_session()

    try:
        data = request.get_json()

        # Validasi & konversi input
        pendapatan          = float(data.get("pendapatan", 0))
        pengeluaran_wajib   = float(data.get("pengeluaran_wajib", 0))
        pengeluaran_tambahan = float(data.get("pengeluaran_tambahan", 0))
        tanggungan          = int(data.get("tanggungan", 0))
        kota                = str(data.get("kota", "Indonesia")).strip() or "Indonesia"

        if pendapatan <= 0:
            return jsonify({"success": False, "error": "Pendapatan harus lebih dari 0."}), 400

        if (pengeluaran_wajib + pengeluaran_tambahan) >= pendapatan:
            return jsonify({
                "success": False,
                "error": "Total pengeluaran melebihi atau sama dengan pendapatan. Periksa kembali angkanya."
            }), 400

        # Panggil Gemini
        result = generate_budget_advice(
            pendapatan=pendapatan,
            pengeluaran_wajib=pengeluaran_wajib,
            pengeluaran_tambahan=pengeluaran_tambahan,
            tanggungan=tanggungan,
            kota=kota
        )

        if result["success"]:
            # Simpan ke session (in-memory, tanpa DB)
            session["budget"] = {
                "input": {
                    "pendapatan": pendapatan,
                    "pengeluaran_wajib": pengeluaran_wajib,
                    "pengeluaran_tambahan": pengeluaran_tambahan,
                    "tanggungan": tanggungan,
                    "kota": kota
                },
                "output": result["data"]
            }
            session.modified = True

        return jsonify(result)

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Input tidak valid: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/budget/reset", methods=["POST"])
def budget_reset():
    """Hapus data budget dari session."""
    session["budget"] = {}
    session.modified = True
    return jsonify({"success": True})


@app.route("/expenses", methods=["GET"])
def expenses():
    """Halaman Expense Analyzer – Week 3."""
    init_session()
    expense_data = session.get("expenses", [])
    expense_insights = session.get("expense_insights", {})
    return render_template(
        "expenses.html",
        page="expenses",
        expenses=expense_data,
        insights=expense_insights,
        categories=EXPENSE_CATEGORIES
    )


@app.route("/expenses/add", methods=["POST"])
def expenses_add():
    """Tambah satu pengeluaran manual ke session."""
    init_session()
    try:
        data = request.get_json()
        tanggal  = str(data.get("tanggal", "")).strip()
        nama     = str(data.get("nama", "")).strip()
        kategori = str(data.get("kategori", "Lainnya")).strip()
        jumlah   = float(data.get("jumlah", 0))

        if not nama:
            return jsonify({"success": False, "error": "Nama pengeluaran tidak boleh kosong."}), 400
        if jumlah <= 0:
            return jsonify({"success": False, "error": "Jumlah harus lebih dari 0."}), 400
        if kategori not in EXPENSE_CATEGORIES:
            kategori = "Lainnya"

        item = {"tanggal": tanggal, "nama": nama, "kategori": kategori, "jumlah": jumlah}
        session["expenses"].append(item)
        # Hapus insight lama karena data berubah
        session["expense_insights"] = {}
        session.modified = True

        return jsonify({"success": True, "data": item, "total": len(session["expenses"])})

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Input tidak valid: {str(e)}"}), 400


@app.route("/expenses/upload-csv", methods=["POST"])
def expenses_upload_csv():
    """
    Terima file CSV dan parse menjadi daftar pengeluaran.
    Format CSV yang diterima (header baris pertama):
      tanggal, nama, kategori, jumlah
    atau minimal:
      nama, jumlah
    """
    init_session()
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "Tidak ada file yang diunggah."}), 400

        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({"success": False, "error": "File harus berformat .csv"}), 400

        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream)

        # Normalisasi nama kolom (case-insensitive, strip spasi)
        raw_rows = list(reader)
        if not raw_rows:
            return jsonify({"success": False, "error": "File CSV kosong."}), 400

        added = 0
        errors = []

        for i, row in enumerate(raw_rows, start=2):  # baris 1 = header
            # Petakan nama kolom fleksibel
            norm = {k.lower().strip(): v.strip() for k, v in row.items() if v}
            nama     = norm.get("nama", norm.get("keterangan", norm.get("description", "")))
            jumlah_s = norm.get("jumlah", norm.get("amount", norm.get("nominal", "0")))
            kategori = norm.get("kategori", norm.get("category", "Lainnya"))
            tanggal  = norm.get("tanggal", norm.get("date", norm.get("tgl", "")))

            if not nama:
                errors.append(f"Baris {i}: kolom 'nama' kosong, dilewati.")
                continue

            try:
                # Bersihkan format angka: hapus titik ribuan & ganti koma desimal
                jumlah_s = jumlah_s.replace("Rp", "").replace(" ", "").replace(".", "").replace(",", ".")
                jumlah = float(jumlah_s)
            except ValueError:
                errors.append(f"Baris {i}: jumlah '{jumlah_s}' tidak valid, dilewati.")
                continue

            if jumlah <= 0:
                errors.append(f"Baris {i}: jumlah harus > 0, dilewati.")
                continue

            if kategori not in EXPENSE_CATEGORIES:
                kategori = "Lainnya"

            session["expenses"].append({
                "tanggal": tanggal, "nama": nama,
                "kategori": kategori, "jumlah": jumlah
            })
            added += 1

        session["expense_insights"] = {}
        session.modified = True

        return jsonify({
            "success": True,
            "added": added,
            "total": len(session["expenses"]),
            "errors": errors[:5]   # maksimal 5 pesan error
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Gagal membaca CSV: {str(e)}"}), 500


@app.route("/expenses/analyze", methods=["POST"])
def expenses_analyze():
    """Kirim semua data expense ke Gemini dan simpan insight ke session."""
    init_session()
    expenses_data = session.get("expenses", [])

    if len(expenses_data) < 2:
        return jsonify({"success": False, "error": "Minimal 2 data pengeluaran untuk dianalisis."}), 400

    # Ambil pendapatan dari budget session jika ada
    pendapatan = session.get("budget", {}).get("input", {}).get("pendapatan", 0)

    result = generate_expense_insights(expenses_data, pendapatan=pendapatan)

    if result["success"]:
        session["expense_insights"] = result["data"]
        session.modified = True

    return jsonify(result)


@app.route("/expenses/delete/<int:idx>", methods=["POST"])
def expenses_delete(idx):
    """Hapus satu item pengeluaran berdasarkan index."""
    init_session()
    exp = session.get("expenses", [])
    if 0 <= idx < len(exp):
        exp.pop(idx)
        session["expenses"] = exp
        session["expense_insights"] = {}
        session.modified = True
        return jsonify({"success": True, "total": len(exp)})
    return jsonify({"success": False, "error": "Index tidak ditemukan."}), 404


@app.route("/expenses/reset", methods=["POST"])
def expenses_reset():
    """Hapus semua data pengeluaran & insight dari session."""
    session["expenses"] = []
    session["expense_insights"] = {}
    session.modified = True
    return jsonify({"success": True})


@app.route("/chatbot")
def chatbot():
    """Halaman AI Financial Advisor (Chatbot) – Week 4."""
    init_session()
    chat_history  = session.get("chat_history", [])
    expenses_list = session.get("expenses", [])
    total_expense = sum(float(e.get("jumlah", 0)) for e in expenses_list)

    return render_template(
        "chatbot.html",
        page="chatbot",
        chat_history=chat_history,
        quick_topics=QUICK_TOPICS,
        budget_data=session.get("budget", {}),
        total_expense=total_expense,
        expense_count=len(expenses_list),
    )


@app.route("/chatbot/send", methods=["POST"])
def chatbot_send():
    """
    Terima pesan dari user, kirim ke Gemini bersama riwayat,
    simpan ke session, kembalikan respons AI sebagai JSON.
    """
    init_session()
    try:
        data  = request.get_json()
        pesan = str(data.get("pesan", "")).strip()

        if not pesan:
            return jsonify({"success": False, "error": "Pesan tidak boleh kosong."}), 400
        if len(pesan) > 1000:
            return jsonify({"success": False, "error": "Pesan terlalu panjang (max 1000 karakter)."}), 400

        # Ambil riwayat chat dari session (format Gemini multi-turn)
        riwayat = session.get("chat_history", [])

        # Kumpulkan konteks keuangan dari session lain
        konteks = {
            "budget":        session.get("budget", {}),
            "total_expense": sum(float(e.get("jumlah", 0)) for e in session.get("expenses", [])),
            "expense_count": len(session.get("expenses", [])),
        }

        # Panggil Gemini
        result = chat_financial_advisor(pesan, riwayat, konteks_keuangan=konteks)

        if not result["success"]:
            return jsonify(result), 500

        # Simpan percakapan ke session dalam format Gemini history
        riwayat.append({"role": "user",  "parts": [pesan]})
        riwayat.append({"role": "model", "parts": [result["teks_respons"]]})

        # Batasi riwayat maksimal 30 pesan (15 turn) agar session tidak membengkak
        if len(riwayat) > 30:
            riwayat = riwayat[-30:]

        session["chat_history"] = riwayat
        session.modified = True

        return jsonify({
            "success":      True,
            "respons":      result["teks_respons"],
            "topik":        result.get("topik", "Umum"),
            "total_pesan":  len(riwayat) // 2,
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/chatbot/reset", methods=["POST"])
def chatbot_reset():
    """Hapus seluruh riwayat percakapan dari session."""
    session["chat_history"] = []
    session.modified = True
    return jsonify({"success": True})


@app.route("/savings")
def savings():
    """Halaman Savings Goal Planner & Investment Guidance – Week 5."""
    init_session()
    savings_goals   = session.get("savings_goals", [])
    savings_plan    = session.get("savings_plan", {})
    invest_guidance = session.get("invest_guidance", {})
    pendapatan      = session.get("budget", {}).get("input", {}).get("pendapatan", 0)

    return render_template(
        "savings.html",
        page="savings",
        savings_goals=savings_goals,
        savings_plan=savings_plan,
        invest_guidance=invest_guidance,
        profil_risiko_list=PROFIL_RISIKO,
        pendapatan=pendapatan,
    )


@app.route("/savings/plan", methods=["POST"])
def savings_plan_generate():
    """Terima data tujuan tabungan, panggil AI, kembalikan rencana."""
    init_session()
    try:
        data = request.get_json()

        nama_tujuan   = str(data.get("nama_tujuan", "")).strip()
        target_jumlah = float(data.get("target_jumlah", 0))
        durasi_bulan  = int(data.get("durasi_bulan", 12))
        tabungan_awal = float(data.get("tabungan_awal", 0))
        prioritas     = str(data.get("prioritas", "sedang"))
        pendapatan    = session.get("budget", {}).get("input", {}).get("pendapatan", 0)

        if not nama_tujuan:
            return jsonify({"success": False, "error": "Nama tujuan tidak boleh kosong."}), 400
        if target_jumlah <= 0:
            return jsonify({"success": False, "error": "Target jumlah harus lebih dari 0."}), 400
        if durasi_bulan < 1 or durasi_bulan > 360:
            return jsonify({"success": False, "error": "Durasi harus antara 1–360 bulan."}), 400
        if tabungan_awal >= target_jumlah:
            return jsonify({"success": False, "error": "Dana awal sudah melebihi atau sama dengan target."}), 400

        goal = {
            "nama_tujuan":   nama_tujuan,
            "target_jumlah": target_jumlah,
            "durasi_bulan":  durasi_bulan,
            "tabungan_awal": tabungan_awal,
            "pendapatan":    pendapatan,
            "prioritas":     prioritas,
        }

        result = generate_savings_plan(goal)

        if result["success"]:
            session["savings_plan"] = result["data"]
            # Simpan goal ke daftar goals
            goals = session.get("savings_goals", [])
            goals.append(goal)
            session["savings_goals"] = goals[-5:]   # simpan max 5 goal terakhir
            session.modified = True

        return jsonify(result)

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Input tidak valid: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/savings/invest", methods=["POST"])
def savings_invest_guidance():
    """Terima profil risiko & dana, panggil AI, kembalikan panduan investasi."""
    init_session()
    try:
        data = request.get_json()

        profil_risiko = str(data.get("profil_risiko", "Sedang")).strip()
        dana          = float(data.get("dana", 0))
        usia          = int(data.get("usia", 0))
        pendapatan    = session.get("budget", {}).get("input", {}).get("pendapatan", 0)

        if profil_risiko not in PROFIL_RISIKO:
            return jsonify({"success": False, "error": "Profil risiko tidak valid."}), 400
        if dana < 0:
            dana = 0

        result = generate_investment_guidance(
            profil_risiko=profil_risiko,
            dana=dana,
            pendapatan=pendapatan,
            usia=usia,
        )

        if result["success"]:
            session["invest_guidance"] = result["data"]
            session.modified = True

        return jsonify(result)

    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Input tidak valid: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route("/savings/reset", methods=["POST"])
def savings_reset():
    """Hapus data savings & investment dari session."""
    session["savings_plan"]    = {}
    session["invest_guidance"] = {}
    session["savings_goals"]   = []
    session.modified = True
    return jsonify({"success": True})


@app.route("/report")
def report():
    """Halaman Laporan & Visualisasi – Week 6."""
    init_session()
    expenses_list   = session.get("expenses",        [])
    budget_data     = session.get("budget",          {})
    savings_plan    = session.get("savings_plan",    {})
    invest_guidance = session.get("invest_guidance", {})
    expense_insights= session.get("expense_insights",{})
    total_expense   = sum(float(e.get("jumlah", 0)) for e in expenses_list)

    # Cek kelengkapan data tiap modul
    has_budget   = bool(budget_data.get("output"))
    has_expenses = len(expenses_list) > 0
    has_savings  = bool(savings_plan.get("tabungan_per_bulan"))
    has_invest   = bool(invest_guidance.get("profil"))
    has_insights = bool(expense_insights.get("insight_utama"))

    return render_template(
        "report.html",
        page="report",
        budget_data=budget_data,
        expenses=expenses_list,
        expense_insights=expense_insights,
        savings_plan=savings_plan,
        invest_guidance=invest_guidance,
        total_expense=total_expense,
        has_budget=has_budget,
        has_expenses=has_expenses,
        has_savings=has_savings,
        has_invest=has_invest,
        has_insights=has_insights,
    )


@app.route("/report/charts", methods=["GET"])
def report_charts():
    """
    Generate semua grafik Matplotlib dan kembalikan sebagai JSON base64.
    Dipanggil async dari JavaScript saat halaman report dibuka.
    """
    init_session()
    expenses_list   = session.get("expenses",     [])
    budget_data     = session.get("budget",       {})
    savings_plan    = session.get("savings_plan", {})
    total_expense   = sum(float(e.get("jumlah", 0)) for e in expenses_list)

    charts = {}

    # Hanya generate chart jika datanya ada (hemat waktu render)
    if expenses_list:
        charts["pie"]     = chart_expense_pie(expenses_list)
        charts["bar"]     = chart_expense_bar(expenses_list)
    if budget_data.get("output"):
        charts["budget"]  = chart_budget_donut(budget_data)
        charts["vs"]      = chart_budget_vs_actual(budget_data, total_expense)
    if savings_plan.get("tabungan_per_bulan"):
        charts["savings"] = chart_savings_projection(savings_plan)

    # Overview hanya jika ada minimal 2 data
    if sum([bool(expenses_list), bool(budget_data.get("output")),
            bool(savings_plan.get("tabungan_per_bulan"))]) >= 2:
        charts["overview"] = chart_dashboard_overview(
            expenses_list, budget_data, total_expense, savings_plan
        )

    return jsonify({"success": True, "charts": charts})


@app.route("/report/download-pdf", methods=["GET"])
def report_download_pdf():
    """Generate dan kirim file PDF laporan keuangan."""
    init_session()
    expenses_list    = session.get("expenses",         [])
    budget_data      = session.get("budget",           {})
    savings_plan     = session.get("savings_plan",     {})
    invest_guidance  = session.get("invest_guidance",  {})
    expense_insights = session.get("expense_insights", {})
    total_expense    = sum(float(e.get("jumlah", 0)) for e in expenses_list)

    # Generate charts untuk PDF
    charts = {}
    if expenses_list:
        charts["pie"] = chart_expense_pie(expenses_list)
    if budget_data.get("output"):
        charts["budget"] = chart_budget_donut(budget_data)
    if savings_plan.get("tabungan_per_bulan"):
        charts["savings"] = chart_savings_projection(savings_plan)
    if sum([bool(expenses_list), bool(budget_data.get("output")),
            bool(savings_plan.get("tabungan_per_bulan"))]) >= 1:
        charts["overview"] = chart_dashboard_overview(
            expenses_list, budget_data, total_expense, savings_plan
        )

    try:
        pdf_bytes = generate_pdf_report(
            budget_data=budget_data,
            expenses=expenses_list,
            expense_insights=expense_insights,
            savings_plan=savings_plan,
            invest_guidance=invest_guidance,
            charts=charts,
        )
        filename = f"laporan-keuangan-financeai.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=5000)
