# AI SEO Audit Tool (POC)

A comprehensive Python + Streamlit application designed to audit any public website URL. It provides an in-depth analysis across four key dimensions: **SEO Foundation**, **Content Quality**, **AI Visibility**, and an overall **Opportunity Score**.

This Proof of Concept (POC) has been highly customized to not only give high-level scores but to provide **granular, location-aware diagnostics** for every check performed (e.g., highlighting the exact HTML tag that failed a check).

---

## 🌟 Key Features

- **Comprehensive Scanning**: Executes over 40 individual checks analyzing keyword placement, heading hierarchy, semantic structure, technical SEO, and AI-readiness (summaries, FAQs, readibility).
- **Detailed Issue Tracking**: Fails/Warnings don't just say "Fix this"; they provide expandable detailed arrays displaying the exact elements (`src`, `href`, or raw HTML snippets) causing the issue.
- **Local SQLite Persistence**: Fully decoupled from external databases. Lead captures and full JSON audit reports are saved locally to `seo_audits.db`.
- **Streamlit Dashboard**: A sleek, dark-themed UI that presents the overall grade, category breakdowns, and individual expandable cards for every check.
- **Exportable Reports**: Generates and persists reports in a JSON structure that can be easily exported or analyzed programmatically.

---

## 🏗️ Project Structure

```text
seo_audit/
├── app.py                    ← Streamlit UI (Frontend entry point)
├── requirements.txt          ← Python dependencies
├── seo_audits.db             ← Local SQLite database (Auto-generated on first run)
├── core/
│   ├── fetcher.py            ← HTTP fetching, BeautifulSoup parsing, and signal extraction
│   ├── checks.py             ← Contains 40+ individual SEO evaluation functions
│   ├── audit_engine.py       ← Orchestrates the fetcher and checks to produce final scores
│   ├── seo_scorer.py         ← Aggregates Technical SEO checks
│   ├── content_scorer.py     ← Aggregates Content Quality checks
│   ├── ai_scorer.py          ← Aggregates AI Visibility checks
│   └── opportunity_scorer.py ← Calculates improvement potential and quick wins
└── utils/
    ├── storage.py            ← SQLite database setup, read/write, and JSON serialization
    └── compat.py             ← Compatibility utilities for data structures
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure you have Python 3.10+ installed. The target URLs you audit must be publicly accessible (no login walls or IP blocks).

### 2. Setup Environment

```bash
# Clone or navigate to the project directory
cd seo_audit

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```
The application will launch in your default browser at `http://localhost:8501`.

---

## 🔍 How the Audit Engine Works

### 1. Fetching & Parsing (`core/fetcher.py`)
When a URL is submitted, the system fetches the HTML and utilizes `BeautifulSoup` to parse it into a `ParsedPage` object. This object holds pre-computed signals like word counts, heading arrays, image links, schema types, and readability scores.

### 2. Executing Checks (`core/checks.py`)
The parsed page and target keyword are passed through a gauntlet of check functions. Every function returns a standardized `CheckResult` dataclass:

```python
@dataclass
class CheckResult:
    name: str           # e.g., "Keyword in title tag"
    score: int          # e.g., 0
    max_score: int      # e.g., 4
    status: str         # "pass", "warn", or "fail"
    found: str          # What was discovered (e.g., "No title tag found")
    impact: str         # Why it matters
    how_to_fix: str     # Actionable advice
    category: str       # e.g., "SEO"
    details: list       # Array of specific HTML snippets or locations related to the issue
```

**The `details` Array**: This is a powerful feature of the POC. If a page has 50 images and 3 are missing `alt` tags, the `details` array will specifically list those 3 images with their `src` and raw HTML code, allowing the user to know exactly what to fix.

### 3. Scoring & Aggregation (`core/audit_engine.py`)
The engine groups the `CheckResult` objects into their respective categories:
- **SEO Foundation** (Max 100)
- **Content Quality** (Max 100)
- **AI Visibility** (Max 100)

The **Opportunity Score** is derived from how many high-impact points were missed. An overall grade is calculated by averaging the modules:
- **0–40**: Poor 🔴
- **41–70**: Average 🟡
- **71–100**: Strong 🟢

### 4. UI Rendering (`app.py`)
Streamlit receives the comprehensive report dictionary. It dynamically renders progress circles for the scores and maps over the checks to build visually distinct cards (Green for pass, Yellow for warn, Red for fail). If a check contains `details`, the UI renders a scrollable "Detailed Issues" box inside the card.

---

## 💾 Local Storage & Data Persistence

The project utilizes a local SQLite database (`seo_audits.db`) handled via `utils/storage.py`. 

- **Auto-Initialization**: The database and tables are created automatically on the first run.
- **Leads Table**: Captures the URL, target keyword, email address, timestamp, and the high-level overall grade.
- **Audit Reports Table**: Stores the full, serialized JSON output of the `audit_engine`. This includes every check, score, and the granular `details` arrays. This allows you to retrieve historical audits without re-fetching the target website.

---

## 🛠️ Extending the Tool

### Adding New Checks
1. Navigate to `core/checks.py`.
2. Write a new function that accepts `(page, kw)`.
3. Evaluate the logic and return a `CheckResult`. Populate the `details` array if applicable.
4. Add the new function to the corresponding scorer module (e.g., `core/seo_scorer.py`).
5. The UI and total max score will automatically adjust to accommodate the new check!
