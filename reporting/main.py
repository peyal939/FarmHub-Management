from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from decouple import AutoConfig
from sqlalchemy import create_engine, text
from datetime import datetime, date, timedelta
from typing import List, Optional
from pathlib import Path


# Ensure we can read the .env from the repo root even when running from the reporting folder
REPO_ROOT = Path(__file__).resolve().parents[1]
config = AutoConfig(search_path=str(REPO_ROOT))

DB_NAME = config("DB_NAME", default="farmhub")
DB_USER = config("DB_USER", default="postgres")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST", default="localhost")
DB_PORT = config("DB_PORT", cast=int, default=5432)

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Lazily create the engine so startup doesn't fail if env isn't loaded yet.
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        # Read-only note: use a DB user with only SELECT privileges for this service.
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


app = FastAPI(title="FarmHub Reporting Service", version="0.1.0")


# Pydantic response models
class FarmSummaryResponse(BaseModel):
    farm_id: int
    farm_name: str
    total_farmers: int
    total_cows: int
    total_milk_production: float


class MilkProductionResponse(BaseModel):
    cow_tag: str
    cow_breed: str
    total_liters: float
    record_count: int


class DailyMilkResponse(BaseModel):
    date: date
    total_liters: float
    cow_count: int


class GeneralSummaryResponse(BaseModel):
    total_farms: int
    total_farmers: int
    total_cows: int
    total_milk_production: float


@app.get("/summary", response_model=GeneralSummaryResponse)
async def get_general_summary():
    """Get overall system summary with totals across all farms."""

    try:
        with get_engine().connect() as connection:
            # Count total farms
            farms_query = text("SELECT COUNT(*) as farm_count FROM farms_farm")
            farms_result = connection.execute(farms_query).fetchone()

            # Count total farmers
            farmers_query = text(
                "SELECT COUNT(*) as farmer_count FROM farms_farmerprofile"
            )
            farmers_result = connection.execute(farmers_query).fetchone()

            # Count total cows
            cows_query = text("SELECT COUNT(*) as cow_count FROM livestock_cow")
            cows_result = connection.execute(cows_query).fetchone()

            # Sum total milk production
            milk_query = text(
                "SELECT COALESCE(SUM(liters), 0) as total_milk FROM production_milkrecord"
            )
            milk_result = connection.execute(milk_query).fetchone()

            return GeneralSummaryResponse(
                total_farms=farms_result.farm_count,
                total_farmers=farmers_result.farmer_count,
                total_cows=cows_result.cow_count,
                total_milk_production=float(milk_result.total_milk),
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving general summary: {str(e)}"
        )


@app.get("/reports/farm/{farm_id}/summary", response_model=FarmSummaryResponse)
async def get_farm_summary(farm_id: int):
    """Get comprehensive summary for a specific farm including farmers, cows, and milk production."""

    try:
        with get_engine().connect() as connection:
            # Query farm details
            farm_query = text(
                """
                SELECT id, name 
                FROM farms_farm 
                WHERE id = :farm_id
            """
            )
            farm_result = connection.execute(
                farm_query, {"farm_id": farm_id}
            ).fetchone()

            if not farm_result:
                raise HTTPException(
                    status_code=404, detail=f"Farm with ID {farm_id} not found"
                )

            # Count farmers for this farm (via FarmerProfile)
            farmers_query = text(
                """
                SELECT COUNT(*) as farmer_count
                FROM farms_farmerprofile 
                WHERE farm_id = :farm_id
            """
            )
            farmers_result = connection.execute(
                farmers_query, {"farm_id": farm_id}
            ).fetchone()

            # Count cows for this farm
            cows_query = text(
                """
                SELECT COUNT(*) as cow_count
                FROM livestock_cow 
                WHERE farm_id = :farm_id
            """
            )
            cows_result = connection.execute(
                cows_query, {"farm_id": farm_id}
            ).fetchone()

            # Sum milk production for this farm's cows
            milk_query = text(
                """
                SELECT COALESCE(SUM(mr.liters), 0) as total_milk
                FROM production_milkrecord mr
                JOIN livestock_cow c ON mr.cow_id = c.id
                WHERE c.farm_id = :farm_id
            """
            )
            milk_result = connection.execute(
                milk_query, {"farm_id": farm_id}
            ).fetchone()

            return FarmSummaryResponse(
                farm_id=farm_result.id,
                farm_name=farm_result.name,
                total_farmers=farmers_result.farmer_count,
                total_cows=cows_result.cow_count,
                total_milk_production=float(milk_result.total_milk),
            )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error retrieving farm summary: {str(e)}"
        )


@app.get(
    "/reports/farm/{farm_id}/milk-production",
    response_model=List[MilkProductionResponse],
)
async def get_farm_milk_production(farm_id: int):
    """Get milk production breakdown by cow for a specific farm."""

    try:
        with get_engine().connect() as connection:
            query = text(
                """
                SELECT 
                    c.tag as cow_tag,
                    c.breed,
                    COALESCE(SUM(mr.liters), 0) as total_liters,
                    COUNT(mr.id) as record_count
                FROM livestock_cow c
                LEFT JOIN production_milkrecord mr ON c.id = mr.cow_id
                WHERE c.farm_id = :farm_id
                GROUP BY c.id, c.tag, c.breed
                ORDER BY total_liters DESC
            """
            )

            result = connection.execute(query, {"farm_id": farm_id}).fetchall()

            return [
                MilkProductionResponse(
                    cow_tag=row.cow_tag,
                    cow_breed=row.breed,
                    total_liters=float(row.total_liters),
                    record_count=row.record_count,
                )
                for row in result
            ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving milk production data: {str(e)}"
        )


@app.get("/reports/farm/{farm_id}/daily-milk", response_model=List[DailyMilkResponse])
async def get_farm_daily_milk(
    farm_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
):
    """Get daily milk production totals for a specific farm within a date range."""

    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date()

        with get_engine().connect() as connection:
            query = text(
                """
                SELECT 
                    mr.date,
                    SUM(mr.liters) as total_liters,
                    COUNT(DISTINCT mr.cow_id) as cow_count
                FROM production_milkrecord mr
                JOIN livestock_cow c ON mr.cow_id = c.id
                WHERE c.farm_id = :farm_id 
                    AND mr.date >= :start_date 
                    AND mr.date <= :end_date
                GROUP BY mr.date
                ORDER BY mr.date DESC
            """
            )

            result = connection.execute(
                query,
                {"farm_id": farm_id, "start_date": start_date, "end_date": end_date},
            ).fetchall()

            return [
                DailyMilkResponse(
                    date=row.date,
                    total_liters=float(row.total_liters),
                    cow_count=row.cow_count,
                )
                for row in result
            ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving daily milk data: {str(e)}"
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    """Lightweight DB connectivity check for diagnostics."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db_error: {e}")


@app.get("/report/summary")
def summary():
    """Simple aggregated counts. Expand later with proper ORM models."""
    with get_engine().connect() as conn:
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
