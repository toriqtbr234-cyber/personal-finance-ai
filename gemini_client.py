"""
gemini_client.py
────────────────
Modul wrapper untuk Google Gemini API.
Berisi semua fungsi prompt engineering yang digunakan di tiap fitur aplikasi.
"""

import os
import json
import google.generativeai as genai
from config import Config


# ── Inisialisasi Gemini ────────────────────────────────────────────────────────
def _get_model():
    """Inisialisasi dan kembalikan model Gemini."""
    genai.configure(api_key=Config.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-1.5-flash")


# ══════════════════════════════════════════════════════════════════════════════
# WEEK 2 — Budget Planner
# ══════════════════════════════════════════════════════════════════════════════

def generate_budget_advice(
    pendapatan: float,
    pengeluaran_wajib: float,
    pengeluaran_tambahan: float,
    tanggungan: int,
    kota: str
) -> dict:
    """
    Hasilkan saran alokasi anggaran berbasis AI menggunakan metode 50/30/20
    yang disesuaikan dengan kondisi pengguna.

    Returns:
        dict dengan key:
            - alokasi     : {kebutuhan, keinginan, tabungan} dalam Rupiah
            - persen      : {kebutuhan, keinginan, tabungan} dalam persen
            - saran_ai    : teks saran naratif dari Gemini
            - tips        : list 3–5 tips spesifik
            - status      : 'sehat' | 'perhatian' | 'kritis'
            - ringkasan   : kalimat singkat status keuangan
    """
    sisa = pendapatan - pengeluaran_wajib - pengeluaran_tambahan
    rasio_pengeluaran = (pengeluaran_wajib + pengeluaran_tambahan) / pendapatan * 100

    prompt = f"""
Kamu adalah konsultan keuangan pribadi berpengalaman untuk pasar Indonesia.
Analisis kondisi keuangan berikut dan berikan saran alokasi anggaran yang SPESIFIK dan ACTIONABLE.

DATA KEUANGAN PENGGUNA:
- Pendapatan bulanan bersih: Rp {pendapatan:,.0f}
- Pengeluaran wajib (cicilan, sewa, tagihan): Rp {pengeluaran_wajib:,.0f}
- Pengeluaran sehari-hari tambahan: Rp {pengeluaran_tambahan:,.0f}
- Jumlah tanggungan: {tanggungan} orang
- Kota tinggal: {kota}
- Sisa uang setelah pengeluaran: Rp {sisa:,.0f}
- Rasio pengeluaran vs pendapatan: {rasio_pengeluaran:.1f}%

TUGAS KAMU:
1. Hitung alokasi anggaran ideal berdasarkan kondisi di atas menggunakan metode 50/30/20 YANG DISESUAIKAN (bukan selalu 50/30/20 kaku, sesuaikan dengan kondisi nyata pengguna).
2. Berikan saran naratif yang hangat, spesifik untuk kondisi di kota {kota}, dan mudah dipahami.
3. Berikan 4 tips konkret dan bisa langsung diterapkan.
4. Tentukan status keuangan: 'sehat', 'perhatian', atau 'kritis'.

PENTING: Balas HANYA dengan JSON valid berikut, tanpa teks lain di luar JSON:

{{
  "alokasi": {{
    "kebutuhan": <angka_rupiah>,
    "keinginan": <angka_rupiah>,
    "tabungan": <angka_rupiah>
  }},
  "persen": {{
    "kebutuhan": <angka_persen>,
    "keinginan": <angka_persen>,
    "tabungan": <angka_persen>
  }},
  "saran_ai": "<paragraf saran naratif 3-4 kalimat, pakai bahasa Indonesia yang hangat>",
  "tips": [
    "<tip konkret 1>",
    "<tip konkret 2>",
    "<tip konkret 3>",
    "<tip konkret 4>"
  ],
  "status": "<sehat|perhatian|kritis>",
  "ringkasan": "<kalimat singkat 1 baris tentang kondisi keuangan pengguna>"
}}
"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Bersihkan jika ada markdown code fence
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        return {"success": True, "data": result}

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Gagal memparse respons AI: {str(e)}",
            "raw": response.text if 'response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Terjadi kesalahan: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════════════
# WEEK 3 — Expense Analyzer
# ══════════════════════════════════════════════════════════════════════════════

# Daftar kategori yang dikenali aplikasi (untuk validasi & UI)
EXPENSE_CATEGORIES = [
    "Makanan & Minuman",
    "Transportasi",
    "Belanja & Pakaian",
    "Kesehatan",
    "Hiburan & Rekreasi",
    "Pendidikan",
    "Tagihan & Utilitas",
    "Tabungan & Investasi",
    "Sosial & Hadiah",
    "Lainnya",
]


def generate_expense_insights(expenses: list, pendapatan: float = 0) -> dict:
    """
    Analisis daftar pengeluaran dan hasilkan insight AI yang mendalam.

    Args:
        expenses : list of dict, tiap item punya key:
                   { tanggal, nama, kategori, jumlah }
        pendapatan: pendapatan bulanan (opsional, untuk konteks rasio)

    Returns:
        dict dengan key:
            - ringkasan_kategori : { kategori: total_rupiah }
            - kategori_terbesar  : nama kategori dengan pengeluaran tertinggi
            - total_pengeluaran  : total semua pengeluaran
            - insight_utama      : paragraf naratif analisis AI
            - area_boros         : list kategori yang berlebihan + alasannya
            - peluang_hemat      : list saran konkret cara berhemat
            - skor_pengeluaran   : angka 1-100 (100 = sangat hemat)
            - label_skor         : 'Sangat Hemat' | 'Cukup Baik' | 'Perlu Perhatian' | 'Boros'
    """
    if not expenses:
        return {"success": False, "error": "Tidak ada data pengeluaran."}

    # Hitung ringkasan per kategori (sisi Python, bukan AI)
    ringkasan = {}
    total = 0.0
    for e in expenses:
        kat = e.get("kategori", "Lainnya")
        jml = float(e.get("jumlah", 0))
        ringkasan[kat] = ringkasan.get(kat, 0) + jml
        total += jml

    kategori_terbesar = max(ringkasan, key=ringkasan.get) if ringkasan else "-"

    # Susun tabel pengeluaran untuk prompt
    tabel_baris = "\n".join(
        f"  - {k}: Rp {v:,.0f} ({v/total*100:.1f}%)"
        for k, v in sorted(ringkasan.items(), key=lambda x: -x[1])
    )

    # Susun 10 transaksi terbesar untuk konteks
    top10 = sorted(expenses, key=lambda x: float(x.get("jumlah", 0)), reverse=True)[:10]
    top10_baris = "\n".join(
        f"  - [{e.get('tanggal','-')}] {e.get('nama','-')} "
        f"({e.get('kategori','Lainnya')}): Rp {float(e.get('jumlah',0)):,.0f}"
        for e in top10
    )

    konteks_pendapatan = (
        f"- Pendapatan bulanan: Rp {pendapatan:,.0f}\n"
        f"- Rasio pengeluaran vs pendapatan: {total/pendapatan*100:.1f}%"
        if pendapatan > 0 else "- Pendapatan: tidak diketahui"
    )

    prompt = f"""
Kamu adalah analis keuangan pribadi berpengalaman untuk pasar Indonesia.
Lakukan analisis mendalam terhadap data pengeluaran berikut dan berikan insight yang SPESIFIK, JUJUR, dan ACTIONABLE.

DATA PENGELUARAN:
- Total pengeluaran: Rp {total:,.0f}
- Jumlah transaksi: {len(expenses)}
{konteks_pendapatan}

RINCIAN PER KATEGORI:
{tabel_baris}

10 TRANSAKSI TERBESAR:
{top10_baris}

TUGAS KAMU:
1. Tulis insight_utama: analisis naratif 3-4 kalimat yang jujur mengenai pola pengeluaran ini. Sebutkan kategori spesifik dan angka nyata.
2. Identifikasi area_boros: kategori mana yang pengeluarannya tidak wajar/berlebihan dan kenapa.
3. Berikan peluang_hemat: 4 saran konkret dan realistis cara menghemat berdasarkan data di atas.
4. Beri skor_pengeluaran: nilai 1-100 berdasarkan efisiensi pengeluaran (pertimbangkan rasio, diversifikasi, dan keseimbangan kategori).

PENTING: Balas HANYA dengan JSON valid berikut, tanpa teks lain:

{{
  "insight_utama": "<analisis naratif 3-4 kalimat, sebutkan angka & kategori spesifik>",
  "area_boros": [
    {{"kategori": "<nama>", "alasan": "<penjelasan singkat kenapa berlebihan>"}},
    {{"kategori": "<nama>", "alasan": "<penjelasan singkat kenapa berlebihan>"}}
  ],
  "peluang_hemat": [
    "<saran konkret 1 dengan estimasi penghematan>",
    "<saran konkret 2 dengan estimasi penghematan>",
    "<saran konkret 3 dengan estimasi penghematan>",
    "<saran konkret 4 dengan estimasi penghematan>"
  ],
  "skor_pengeluaran": <angka 1-100>,
  "label_skor": "<Sangat Hemat|Cukup Baik|Perlu Perhatian|Boros>"
}}
"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        ai_result = json.loads(raw)

        return {
            "success": True,
            "data": {
                "ringkasan_kategori": ringkasan,
                "kategori_terbesar": kategori_terbesar,
                "total_pengeluaran": total,
                "jumlah_transaksi": len(expenses),
                **ai_result,
            }
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Gagal memparse respons AI: {str(e)}",
            "raw": response.text if 'response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Terjadi kesalahan: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════════════
# WEEK 4 — AI Financial Advisor Chatbot
# ══════════════════════════════════════════════════════════════════════════════

# Topik-topik keuangan yang dikenali untuk quick replies
QUICK_TOPICS = [
    "Bagaimana cara mulai menabung?",
    "Apa itu dana darurat dan berapa idealnya?",
    "Jelaskan perbedaan reksa dana dan saham",
    "Tips mengurangi pengeluaran bulanan",
    "Bagaimana cara melunasi hutang lebih cepat?",
    "Apa investasi yang cocok untuk pemula?",
]

# System prompt yang mendefinisikan kepribadian & batasan chatbot
_SYSTEM_PROMPT = """Kamu adalah FinanceAI, asisten keuangan pribadi yang ramah, cerdas, dan terpercaya untuk pengguna di Indonesia.

KEPRIBADIAN:
- Hangat, suportif, dan tidak menghakimi kondisi keuangan pengguna
- Menggunakan bahasa Indonesia yang natural dan mudah dipahami
- Menyebut angka dalam format Rupiah (Rp) yang mudah dibaca
- Sesekali menggunakan emoji yang relevan untuk membuat respons lebih menarik

KEAHLIAN:
- Perencanaan anggaran dan manajemen pengeluaran
- Strategi menabung dan dana darurat
- Pengenalan instrumen investasi (reksa dana, saham, obligasi, deposito, emas)
- Pelunasan hutang dan manajemen kredit
- Perencanaan keuangan jangka panjang (rumah, pendidikan, pensiun)
- Literasi keuangan dasar

ATURAN RESPONS:
1. Jawab HANYA pertanyaan seputar keuangan pribadi. Jika ditanya hal lain, tolak dengan sopan dan arahkan kembali ke topik keuangan.
2. Selalu berikan jawaban yang TERSTRUKTUR dengan jelas menggunakan format berikut jika relevan:
   - Gunakan **teks tebal** untuk poin penting
   - Gunakan angka (1. 2. 3.) untuk langkah-langkah
   - Gunakan bullet (-) untuk daftar opsi
   - Pisahkan bagian dengan baris kosong
3. Sertakan KONTEKS INDONESIA: sebutkan contoh produk/instrumen yang tersedia di Indonesia (ORI, SBR, reksa dana Bibit/Bareksa, dll) jika relevan.
4. Akhiri dengan satu PERTANYAAN LANJUTAN yang membantu pengguna berpikir lebih dalam, atau satu TIPS SINGKAT yang actionable.
5. Jaga panjang respons: tidak terlalu pendek (min 3 paragraf) namun tidak bertele-tele (max ~300 kata).
6. JANGAN memberikan saran investasi spesifik yang bisa dianggap sebagai rekomendasi profesional. Selalu ingatkan bahwa keputusan akhir ada di tangan pengguna.
"""


def chat_financial_advisor(
    pesan: str,
    riwayat: list,
    konteks_keuangan: dict = None
) -> dict:
    """
    Jawab pertanyaan keuangan pengguna dengan riwayat percakapan multi-turn.

    Args:
        pesan             : Pesan terbaru dari pengguna
        riwayat           : List of dict [{"role": "user"|"model", "parts": [teks]}]
        konteks_keuangan  : Data keuangan dari sesi (budget, expense) untuk konteks tambahan

    Returns:
        dict: { success, teks_respons, topik_terdeteksi }
    """
    if not pesan.strip():
        return {"success": False, "error": "Pesan tidak boleh kosong."}

    # Bangun konteks keuangan pengguna jika tersedia
    konteks_str = ""
    if konteks_keuangan:
        budget_in  = konteks_keuangan.get("budget", {}).get("input", {})
        budget_out = konteks_keuangan.get("budget", {}).get("output", {})
        total_exp  = konteks_keuangan.get("total_expense", 0)
        exp_count  = konteks_keuangan.get("expense_count", 0)

        if budget_in.get("pendapatan"):
            konteks_str += f"\n\nDATA KEUANGAN PENGGUNA SAAT INI (gunakan sebagai konteks jika relevan):"
            konteks_str += f"\n- Pendapatan bulanan: Rp {budget_in['pendapatan']:,.0f}"
            konteks_str += f"\n- Kota: {budget_in.get('kota', '-')}"
            if budget_out.get("status"):
                konteks_str += f"\n- Status keuangan: {budget_out['status']}"
            if total_exp:
                konteks_str += f"\n- Total pengeluaran tercatat: Rp {total_exp:,.0f} ({exp_count} transaksi)"

    # System prompt + konteks
    system_with_context = _SYSTEM_PROMPT + konteks_str

    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_with_context
        )

        # Bangun riwayat chat untuk multi-turn
        chat = model.start_chat(history=riwayat)

        # Kirim pesan terbaru
        response = chat.send_message(pesan)
        teks = response.text.strip()

        # Deteksi topik (sederhana, untuk UI labeling)
        topik = _deteksi_topik(pesan)

        return {
            "success": True,
            "teks_respons": teks,
            "topik": topik,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Gagal menghubungi AI: {str(e)}"
        }


def _deteksi_topik(pesan: str) -> str:
    """Deteksi topik keuangan dari pesan untuk labeling UI (tanpa AI, rule-based)."""
    pesan_lower = pesan.lower()
    if any(k in pesan_lower for k in ["tabung", "nabung", "simpan"]):
        return "Tabungan"
    if any(k in pesan_lower for k in ["investasi", "saham", "reksa dana", "obligasi", "emas", "deposito"]):
        return "Investasi"
    if any(k in pesan_lower for k in ["hutang", "kredit", "cicilan", "kpr", "pinjam"]):
        return "Hutang & Kredit"
    if any(k in pesan_lower for k in ["anggaran", "budget", "pengeluaran", "hemat", "boros"]):
        return "Anggaran"
    if any(k in pesan_lower for k in ["darurat", "emergency", "dana darurat"]):
        return "Dana Darurat"
    if any(k in pesan_lower for k in ["pensiun", "retire", "masa tua"]):
        return "Pensiun"
    return "Umum"


# ══════════════════════════════════════════════════════════════════════════════
# WEEK 5 — Savings Goal Planner & Investment Guidance
# ══════════════════════════════════════════════════════════════════════════════

def generate_savings_plan(goal: dict) -> dict:
    """
    Buat rencana tabungan bulanan lengkap berbasis AI.

    Args:
        goal: {
            nama_tujuan    : str   — nama tujuan (misal: "Beli rumah")
            target_jumlah  : float — jumlah yang ingin dikumpulkan (Rp)
            durasi_bulan   : int   — berapa bulan targetnya
            tabungan_awal  : float — dana yang sudah dimiliki saat ini
            pendapatan     : float — pendapatan bulanan (opsional, 0 jika tidak diisi)
            prioritas      : str   — 'rendah' | 'sedang' | 'tinggi'
        }

    Returns:
        dict: {
            success, data: {
                tabungan_per_bulan   : float
                total_ditabung       : float
                bunga_estimasi       : float   (asumsi 4%/tahun di tabungan biasa)
                total_dengan_bunga   : float
                persen_pendapatan    : float   (jika pendapatan diisi)
                strategi_utama       : str     (narasi singkat strategi AI)
                langkah_langkah      : list    (5 langkah konkret)
                instrumen_saran      : list    (daftar instrumen tabungan yang disarankan)
                milestone            : list    (checkpoint per kuartal)
                tips_percepatan      : list    (cara mempercepat jika mau)
                feasibility          : 'mudah' | 'menantang' | 'berat'
                catatan_ai           : str     (pesan penyemangat dari AI)
            }
        }
    """
    nama          = goal.get("nama_tujuan", "Tujuan Tabungan")
    target        = float(goal.get("target_jumlah", 0))
    durasi        = int(goal.get("durasi_bulan", 12))
    awal          = float(goal.get("tabungan_awal", 0))
    pendapatan    = float(goal.get("pendapatan", 0))
    prioritas     = goal.get("prioritas", "sedang")

    if target <= 0 or durasi <= 0:
        return {"success": False, "error": "Target dan durasi harus lebih dari 0."}

    sisa_target    = max(target - awal, 0)
    nabung_minimal = sisa_target / durasi if durasi > 0 else sisa_target
    persen_pend    = (nabung_minimal / pendapatan * 100) if pendapatan > 0 else 0

    prompt = f"""
Kamu adalah perencana keuangan pribadi ahli untuk pasar Indonesia.
Buat rencana tabungan yang DETAIL, REALISTIS, dan MOTIVATIF berdasarkan data berikut.

DATA TUJUAN TABUNGAN:
- Nama tujuan: {nama}
- Target dana: Rp {target:,.0f}
- Dana awal yang sudah dimiliki: Rp {awal:,.0f}
- Sisa yang perlu dikumpulkan: Rp {sisa_target:,.0f}
- Durasi target: {durasi} bulan ({durasi/12:.1f} tahun)
- Tabungan minimal per bulan: Rp {nabung_minimal:,.0f}
- Pendapatan bulanan: {"Rp " + f"{pendapatan:,.0f}" if pendapatan > 0 else "tidak diketahui"}
- Persentase dari pendapatan: {f"{persen_pend:.1f}%" if pendapatan > 0 else "tidak diketahui"}
- Tingkat prioritas: {prioritas}

TUGAS KAMU:
1. Hitung tabungan_per_bulan yang IDEAL (boleh lebih dari minimal jika logis berdasarkan konteks).
2. Buat strategi_utama: narasi 2-3 kalimat yang spesifik dan relevan untuk tujuan "{nama}" di Indonesia.
3. Susun 5 langkah_langkah konkret yang bisa langsung dilakukan.
4. Rekomendasikan 3 instrumen_saran yang cocok untuk tujuan ini (contoh: reksa dana pasar uang, deposito, SBN, dll) beserta alasan singkat.
5. Buat 4 milestone (titik pencapaian per kuartal atau per fase) dengan nama yang memotivasi.
6. Berikan 3 tips_percepatan jika pengguna ingin mencapai tujuan lebih cepat.
7. Tentukan feasibility: 'mudah' (< 15% pendapatan atau durasi > 24 bln), 'menantang' (15-30%), 'berat' (> 30% atau durasi < 6 bln).
8. Tulis catatan_ai: 1-2 kalimat penyemangat yang personal dan relevan dengan tujuan "{nama}".

PENTING: Balas HANYA dengan JSON valid berikut, tanpa teks lain:

{{
  "tabungan_per_bulan": <angka_rupiah>,
  "strategi_utama": "<narasi 2-3 kalimat spesifik>",
  "langkah_langkah": [
    "<langkah konkret 1>",
    "<langkah konkret 2>",
    "<langkah konkret 3>",
    "<langkah konkret 4>",
    "<langkah konkret 5>"
  ],
  "instrumen_saran": [
    {{"nama": "<nama instrumen>", "alasan": "<kenapa cocok>", "estimasi_return": "<persentase/tahun>"}},
    {{"nama": "<nama instrumen>", "alasan": "<kenapa cocok>", "estimasi_return": "<persentase/tahun>"}},
    {{"nama": "<nama instrumen>", "alasan": "<kenapa cocok>", "estimasi_return": "<persentase/tahun>"}}
  ],
  "milestone": [
    {{"fase": "<nama fase>", "target_persen": <0-100>, "deskripsi": "<apa yang sudah tercapai>"}},
    {{"fase": "<nama fase>", "target_persen": <0-100>, "deskripsi": "<apa yang sudah tercapai>"}},
    {{"fase": "<nama fase>", "target_persen": <0-100>, "deskripsi": "<apa yang sudah tercapai>"}},
    {{"fase": "<nama fase>", "target_persen": 100, "deskripsi": "<tujuan tercapai!>"}}
  ],
  "tips_percepatan": [
    "<tip percepatan 1>",
    "<tip percepatan 2>",
    "<tip percepatan 3>"
  ],
  "feasibility": "<mudah|menantang|berat>",
  "catatan_ai": "<1-2 kalimat penyemangat personal>"
}}
"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        ai = json.loads(raw)

        # Hitung angka tambahan di sisi Python
        nabung_bulanan = float(ai.get("tabungan_per_bulan", nabung_minimal))
        total_ditabung = nabung_bulanan * durasi + awal
        # Estimasi bunga sederhana (bunga rata-rata deposito 4%/tahun, compound bulanan)
        r = 0.04 / 12
        total_bunga = nabung_bulanan * (((1 + r) ** durasi - 1) / r) * (1 + r) + awal * (1 + r) ** durasi

        return {
            "success": True,
            "data": {
                **ai,
                "tabungan_per_bulan":  nabung_bulanan,
                "total_ditabung":      round(total_ditabung, 0),
                "bunga_estimasi":      round(total_bunga - total_ditabung, 0),
                "total_dengan_bunga":  round(total_bunga, 0),
                "persen_pendapatan":   round(persen_pend, 1),
                "target_jumlah":       target,
                "durasi_bulan":        durasi,
                "tabungan_awal":       awal,
                "nama_tujuan":         nama,
            }
        }

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Gagal memparse respons AI: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Terjadi kesalahan: {str(e)}"}


# ── Daftar profil risiko yang valid ──────────────────────────────────────────
PROFIL_RISIKO = ["Rendah", "Sedang", "Tinggi"]


def generate_investment_guidance(profil_risiko: str, dana: float,
                                  pendapatan: float = 0, usia: int = 0) -> dict:
    """
    Hasilkan panduan investasi dasar sesuai profil risiko pengguna.

    Args:
        profil_risiko : 'Rendah' | 'Sedang' | 'Tinggi'
        dana          : dana yang tersedia untuk investasi (Rp)
        pendapatan    : pendapatan bulanan (opsional)
        usia          : usia pengguna (opsional, untuk saran jangka panjang)

    Returns:
        dict: {
            success, data: {
                profil          : str
                deskripsi_profil: str
                alokasi         : list — breakdown % per aset
                instrumen       : list — daftar instrumen dengan detail
                strategi_masuk  : str  — cara masuk ke pasar
                waktu_ideal     : str  — horizon investasi yang disarankan
                risiko_utama    : list — risiko yang perlu diwaspadai
                langkah_mulai   : list — 5 langkah konkret memulai
                catatan_penting : str  — disclaimer & pesan penting
            }
        }
    """
    if profil_risiko not in PROFIL_RISIKO:
        profil_risiko = "Sedang"

    konteks_dana = f"Rp {dana:,.0f}" if dana > 0 else "belum ditentukan"
    konteks_pend = f"Rp {pendapatan:,.0f}/bulan" if pendapatan > 0 else "tidak diketahui"
    konteks_usia = f"{usia} tahun" if usia > 0 else "tidak diketahui"

    # Karakteristik tiap profil untuk panduan prompt
    profil_desc = {
        "Rendah":  "menghindari risiko, prioritas keamanan modal, cocok untuk dana darurat atau tujuan jangka pendek (<3 tahun)",
        "Sedang":  "toleran terhadap fluktuasi moderat, menyeimbangkan pertumbuhan dan keamanan, cocok untuk tujuan 3-7 tahun",
        "Tinggi":  "siap menghadapi volatilitas tinggi demi potensi return maksimal, cocok untuk tujuan jangka panjang (>7 tahun)",
    }

    prompt = f"""
Kamu adalah konsultan investasi berpengalaman untuk pasar Indonesia (bukan financial advisor profesional berlisensi).
Berikan panduan investasi yang EDUKATIF, SPESIFIK untuk instrumen di Indonesia, dan ACTIONABLE.

DATA INVESTOR:
- Profil risiko: {profil_risiko} ({profil_desc[profil_risiko]})
- Dana investasi tersedia: {konteks_dana}
- Pendapatan bulanan: {konteks_pend}
- Usia: {konteks_usia}

TUGAS KAMU:
1. Jelaskan deskripsi_profil investor ini dalam 2 kalimat yang memvalidasi pilihan mereka.
2. Buat alokasi aset yang spesifik (jumlah persen harus total 100%).
3. Rekomendasikan 4-5 instrumen investasi yang TERSEDIA DI INDONESIA dan cocok untuk profil ini,
   lengkap dengan contoh produk nyata (misal: Reksa Dana Pasar Uang Schroder, ORI, SBN, saham blue chip BBCA/BBRI/TLKM, dll).
4. Jelaskan strategi_masuk: cara terbaik memulai investasi dengan profil ini (DCA, lump sum, dll).
5. Tentukan waktu_ideal: horizon investasi yang disarankan.
6. Sebutkan 3 risiko_utama yang perlu diwaspadai profil ini.
7. Susun 5 langkah_mulai yang bisa dilakukan minggu ini.
8. Tulis catatan_penting: disclaimer singkat bahwa ini bukan saran investasi profesional.

PENTING: Balas HANYA dengan JSON valid berikut, tanpa teks lain:

{{
  "profil": "{profil_risiko}",
  "deskripsi_profil": "<2 kalimat yang memvalidasi pilihan profil ini>",
  "alokasi": [
    {{"aset": "<nama kelas aset>", "persen": <angka>, "warna": "<hex color>", "keterangan": "<singkat>"}},
    {{"aset": "<nama kelas aset>", "persen": <angka>, "warna": "<hex color>", "keterangan": "<singkat>"}},
    {{"aset": "<nama kelas aset>", "persen": <angka>, "warna": "<hex color>", "keterangan": "<singkat>"}}
  ],
  "instrumen": [
    {{
      "nama": "<nama instrumen>",
      "contoh_produk": "<contoh nyata di Indonesia>",
      "estimasi_return": "<range return/tahun>",
      "min_investasi": "<nominal minimum>",
      "cocok_untuk": "<penjelasan singkat>",
      "platform": "<di mana bisa beli>"
    }}
  ],
  "strategi_masuk": "<penjelasan strategi DCA/lump sum/dll, 2-3 kalimat>",
  "waktu_ideal": "<horizon waktu yang disarankan dan alasannya>",
  "risiko_utama": [
    "<risiko 1 yang perlu diwaspadai>",
    "<risiko 2 yang perlu diwaspadai>",
    "<risiko 3 yang perlu diwaspadai>"
  ],
  "langkah_mulai": [
    "<langkah konkret 1 yang bisa dilakukan minggu ini>",
    "<langkah konkret 2>",
    "<langkah konkret 3>",
    "<langkah konkret 4>",
    "<langkah konkret 5>"
  ],
  "catatan_penting": "<disclaimer singkat 1-2 kalimat>"
}}
"""

    try:
        model = _get_model()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        ai = json.loads(raw)

        return {
            "success": True,
            "data": {
                **ai,
                "dana_investasi": dana,
                "pendapatan":     pendapatan,
                "usia":           usia,
            }
        }

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Gagal memparse respons AI: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Terjadi kesalahan: {str(e)}"}
