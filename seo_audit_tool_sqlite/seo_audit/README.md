# AI SEO Audit Tool

A Python + Streamlit application that audits any public website URL and scores it across four dimensions:
SEO Foundation, Content Quality, AI Visibility, and Opportunity Score.

---

## Project Structure

```
seo_audit/
├── app.py                    ← Streamlit UI (entry point)
├── requirements.txt
├── .env.example              ← Copy to .env and fill in
├── supabase_schema.sql       ← Run once in Supabase SQL editor
├── .streamlit/
│   └── config.toml           ← Theme & server settings
├── core/
│   ├── __init__.py
│   ├── fetcher.py            ← HTTP fetch + HTML parse
│   ├── audit_engine.py       ← Orchestrates all modules
│   ├── seo_scorer.py         ← SEO Foundation scoring
│   ├── content_scorer.py     ← Content Quality scoring
│   ├── ai_scorer.py          ← AI Visibility scoring
│   └── opportunity_scorer.py ← Opportunity Score + recommendations
└── utils/
    ├── __init__.py
    └── storage.py            ← Supabase lead/audit persistence
```

---

## Quick Start

### 1. Clone / copy the project

```bash
cd seo_audit
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase credentials:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
```

If you don't have Supabase yet, the tool still works — audit results just won't be persisted.

### 4. Set up Supabase (optional but recommended for lead capture)

1. Create a free project at https://supabase.com
2. Go to SQL Editor and run the contents of `supabase_schema.sql`
3. Copy your project URL and anon key from Settings → API

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at http://localhost:8501

---

## Scoring Logic

| Module | Max | Key checks |
|---|---|---|
| SEO Foundation | 100 | Title, meta, H1, H2, alt tags, indexability, internal links |
| Content Quality | 100 | Word count, paragraph size, heading ratio, depth signals |
| AI Visibility | 100 | FAQ, summary, para length, readability, headings, direct answers, definitions |
| Opportunity Score | 100 | Critical gaps, improvement potential, quick wins |
| **Overall** | **100** | Average of all four modules |

Grades: **0–40 Poor · 41–70 Average · 71–100 Strong**

Scoring logic is entirely server-side and is NOT exposed in the UI.

---

## Deployment

### Streamlit Community Cloud (free)

1. Push the project to a GitHub repo
2. Go to https://share.streamlit.io → New app
3. Set the main file to `app.py`
4. Add your environment variables in the Secrets panel (TOML format):
   ```toml
   SUPABASE_URL = "https://..."
   SUPABASE_KEY = "..."
   ```

### Self-hosted (VPS / Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Customisation

### Adding your branding
- Edit the hero text in `app.py` (search for `hero-title`)
- Update the CTA buttons and contact details at the bottom of `app.py`
- Replace the favicon in `.streamlit/config.toml`

### Extending scoring
- Each module (`seo_scorer.py`, `content_scorer.py`, etc.) is self-contained
- Add new `CheckResult` items to any module's `score()` function
- The `max_score` values normalise automatically — no other changes needed

### Connecting CTA buttons
The two CTA buttons at the bottom ("Get Full AI SEO Report" and "Request Detailed Audit")
currently just render as UI. Connect them to:
- A Calendly embed (use `st.components.v1.html`)
- A mailto link
- A separate Streamlit page or form

---

## Data & Privacy

- **What is stored**: URL, email, domain, scores, grade, fetch time, and any error messages
- **What is NOT stored**: Full page HTML, extracted text, or any PII beyond email
- Supabase RLS is configured to block public reads — only your service_role key can query data
- Add a privacy notice to your deployed page informing users their email is stored

---

## Requirements

- Python 3.10+
- The target URL must be publicly accessible (no login walls, no IP blocks)
- `textstat` is used for Flesch–Kincaid readability; gracefully degrades if unavailable
