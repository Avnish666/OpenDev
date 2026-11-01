
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

app = FastAPI(
    title="Open Source Funding API",
    version="0.1.0"
)

from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=[
        "GET", "POST", "PUT", "PATCH", "DELETE"
    ],
    allow_headers=[
        "Content-Type",
        "Authorization"
    ],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/db-health")
def database_health(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar_one()

        return {
            "status": "connected",
            "database": "PostgreSQL",
            "result": result
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
