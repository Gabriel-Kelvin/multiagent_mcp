from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    DB_PATH: str = os.getenv("DB_PATH", "logs/app.db")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/events.jsonl")
    ENV: str = os.getenv("ENV", "dev")
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    # External data source (relational)
    DATA_DB_TYPE: str = os.getenv("DATA_DB_TYPE", "")  # mysql | postgres | sqlite
    DATA_HOST: str = os.getenv("DATA_HOST", "")
    DATA_PORT: str = os.getenv("DATA_PORT", "")
    DATA_NAME: str = os.getenv("DATA_NAME", "")
    DATA_USER: str = os.getenv("DATA_USER", "")
    DATA_PASSWORD: str = os.getenv("DATA_PASSWORD", "")
    DATA_TABLE: str = os.getenv("DATA_TABLE", "")
    # Optional for Postgres/Supabase data source
    DATA_DSN: str = os.getenv("DATA_DSN", "")
    DATA_SSLMODE: str = os.getenv("DATA_SSLMODE", "")

    # Supabase/Postgres (internal app store)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    # Prefer pooler DSN for app connections; fall back to direct
    SUPABASE_POOLER_DSN: str = os.getenv("SUPABASE_POOLER_DSN", "")
    SUPABASE_DIRECT_DSN: str = os.getenv("SUPABASE_DIRECT_DSN", "")
    # Optional discrete PG params (used if DSN is not provided)
    PGHOST: str = os.getenv("PGHOST", "")
    PGPORT: str = os.getenv("PGPORT", "")
    PGDATABASE: str = os.getenv("PGDATABASE", "")
    PGUSER: str = os.getenv("PGUSER", "")
    PGPASSWORD: str = os.getenv("PGPASSWORD", "")

settings = Settings()
