# Multi-Agent Data Assistant

- Python 3.10+
- LangGraph + LangChain
- SendGrid for email
- APScheduler for scheduling
- SQLite for state + logs
- fpdf2 for PDF generation

## Setup

1. Create and fill `.env` from `.env.example`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run a demo flow: `python main.py`.

## Flow

User input -> NLP Agent -> CSV -> Email Agent -> Logs.

## Notes

- Email sending is skipped if SendGrid config is missing.
- NLP uses OpenAI when configured; otherwise a safe mock path.
