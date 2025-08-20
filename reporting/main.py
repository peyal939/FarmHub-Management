from fastapi import FastAPI
from decouple import config
from sqlalchemy import create_engine, text


DB_NAME = config("DB_NAME", default="farmhub")
DB_USER = config("DB_USER", default="postgres")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST", default="localhost")
DB_PORT = config("DB_PORT", cast=int, default=5432)

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Read-only note: use a DB user with only SELECT privileges for this service.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

app = FastAPI(title="FarmHub Reporting Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/report/summary")
def summary():
    """Simple aggregated counts. Expand later with proper ORM models."""
    with engine.connect() as conn:
        counts = {}
        for table in [
            "accounts_user",
            "farms_farm",
            "farms_farmerprofile",
            "livestock_cow",
            "livestock_activity",
            "production_milkrecord",
        ]:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar_one()
            except Exception as e:
                counts[table] = f"error: {e}"  # helpful during setup
        return counts
