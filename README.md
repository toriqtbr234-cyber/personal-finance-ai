# ◈ FinanceAI — AI-Powered Personal Finance Assistant

> Asisten keuangan pribadi berbasis AI yang dibangun dengan **Python + Flask + Google Gemini API**

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black?style=flat-square&logo=flask)
![Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-orange?style=flat-square&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 About This Project

**FinanceAI** is a locally-deployed web-based personal finance assistant that leverages
Google Gemini AI to help users manage their finances effectively. Built as a capstone
project for the AI Developer Program at Parahyangan Catholic University.

| Info | Detail |
|---|---|
| **Student** | Muhamad Toriq Thabrani |
| **Student ID** | 6162201034 |
| **Institution** | Parahyangan Catholic University |
| **Program** | AI Developer Program |

---

## ✨ Features

| Feature | Description |
|---|---|
| 💰 **Budget Planner** | AI-generated 50/30/20 budget allocation based on income, expenses, city, and dependants |
| 📊 **Expense Analyzer** | Manual or CSV expense input with AI-driven spending insights and efficiency score |
| 🤖 **AI Financial Advisor** | Multi-turn conversational chatbot powered by Gemini with financial context awareness |
| 🎯 **Savings Goal Planner** | AI-generated monthly savings plan with milestone tracking and compound interest projection |
| 📈 **Investment Guidance** | Risk-profile-based investment recommendations with Indonesian instrument examples |
| 📄 **Report & Visualisation** | Matplotlib charts (5 types) + downloadable 4-page PDF report via ReportLab |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.x, Flask 3.0.3
- **AI Engine:** Google Gemini 1.5 Flash API
- **Visualisation:** Matplotlib 3.9.0
- **PDF Generation:** ReportLab 4.2.2
- **Data Processing:** Pandas 2.2.2
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Jinja2
- **Storage:** Flask Session (in-memory, no database)

---

## 🗂️ Project Structure

```
personal-finance-ai/
├── app.py                  ← Flask app + 20 routes
├── gemini_client.py        ← All Gemini AI functions + prompt engineering
├── chart_generator.py      ← 6 Matplotlib chart functions
├── report_generator.py     ← ReportLab PDF generator (4-page report)
├── config.py               ← Environment variable loader
├── requirements.txt        ← Python dependencies
├── .env.example            ← Environment variable template
├── static/
│   ├── css/style.css       ← Custom dark-theme design system
│   └── js/main.js          ← Shared JavaScript utilities
└── templates/
    ├── base.html           ← Master layout (sidebar + topbar)
    ├── index.html          ← Dashboard
    ├── budget.html         ← Budget Planner
    ├── expenses.html       ← Expense Analyzer
    ├── chatbot.html        ← AI Financial Advisor
    ├── savings.html        ← Savings Goal & Investment Guidance
    └── report.html         ← Report & Visualisation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- A Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/toriqtbr234-cyber/personal-finance-ai.git
cd personal-finance-ai
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and fill in your values:
```
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_SECRET_KEY=any_long_random_string_here
```

**5. Run the application**
```bash
python app.py
```

**6. Open in browser**

Navigate to **http://localhost:5000**

---

## 📱 Application Pages

| Page | Route | Description |
|---|---|---|
| Dashboard | `/` | Financial summary hub |
| Budget Planner | `/budget` | AI budget allocation |
| Expense Analyzer | `/expenses` | Expense tracking + AI insights |
| AI Advisor | `/chatbot` | Conversational financial advisor |
| Savings & Invest | `/savings` | Savings goal + investment guidance |
| Report | `/report` | Charts + PDF report download |

---

## ⚠️ Important Notes

- **No database required** — all data is stored in Flask session (resets on server restart)
- **Never commit your `.env` file** — it contains your private API key
- **Local use only** — the app runs on `localhost:5000` and is not deployed to a server
- **Gemini free tier** — rapid successive AI calls may hit rate limits; wait a few seconds between requests

---

## 📄 License

This project is created for academic purposes as part of the AI Developer Program capstone project.

---

<div align="center">
  <strong>◈ FinanceAI</strong> · Built with Python, Flask & Google Gemini AI<br>
  Muhamad Toriq Thabrani · 6162201034 · Parahyangan Catholic University
</div>
