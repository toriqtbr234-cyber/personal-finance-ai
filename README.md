# FinanceAI — Personal Finance Assistant 💰

Asisten keuangan pribadi berbasis AI yang dibangun dengan **Python + Flask + Gemini API**.

---

## 🗂️ Struktur Proyek

```
personal-finance-ai/
├── app.py                  ← Flask app utama + routing
├── config.py               ← Konfigurasi environment
├── requirements.txt        ← Daftar library Python
├── .env.example            ← Template environment variables
├── static/
│   ├── css/style.css       ← Desain & tampilan
│   └── js/main.js          ← Utilitas JavaScript
└── templates/
    ├── base.html           ← Layout utama (sidebar + topbar)
    ├── index.html          ← Dashboard (Week 1 ✅)
    ├── budget.html         ← Budget Planner (Week 2)
    ├── expenses.html       ← Expense Analyzer (Week 3)
    ├── chatbot.html        ← AI Advisor / Chatbot (Week 4)
    ├── savings.html        ← Savings & Investment (Week 5)
    └── report.html         ← Laporan & Visualisasi (Week 6)
```

---

## 🚀 Cara Menjalankan (Setup Week 1)

### 1. Clone / Buat Folder Proyek
```bash
mkdir personal-finance-ai
cd personal-finance-ai
```

### 2. Buat Virtual Environment
```bash
python -m venv venv

# Aktifkan (Windows)
venv\Scripts\activate

# Aktifkan (Mac/Linux)
source venv/bin/activate
```

### 3. Install Library
```bash
pip install -r requirements.txt
```

### 4. Siapkan File .env
```bash
cp .env.example .env
```
Kemudian buka file `.env` dan isi:
```
GEMINI_API_KEY=masukkan_api_key_gemini_kamu
FLASK_SECRET_KEY=buat_string_acak_panjang_di_sini
```

### 5. Dapatkan Gemini API Key
1. Buka https://aistudio.google.com/app/apikey
2. Klik **Create API Key**
3. Copy dan paste ke file `.env`

### 6. Jalankan Aplikasi
```bash
python app.py
```
Buka browser → **http://localhost:5000**

---

## 📅 Progress Pengerjaan

| Minggu | Fitur                          | Status     |
|--------|--------------------------------|------------|
| 1      | Setup + Basic UI Framework     | ✅ Selesai  |
| 2      | Budget Planner                 | 🔜 Akan dikerjakan |
| 3      | Expense Analyzer               | 🔜 Akan dikerjakan |
| 4      | AI Chatbot / Advisor           | 🔜 Akan dikerjakan |
| 5      | Savings Goal & Investment      | 🔜 Akan dikerjakan |
| 6      | Visualisasi & Report           | 🔜 Akan dikerjakan |

---

## 🔧 VS Code Extensions yang Direkomendasikan

- **Python** (Microsoft)
- **Pylance**
- **Flask Snippets**
- **Jinja2 Snippets**
- **dotenv** (file .env highlighting)
- **Thunder Client** (test API endpoints)
