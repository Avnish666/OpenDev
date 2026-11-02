
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

app = FastAPI(
    title="Open Source Funding API",
    version="0.1.0"
)

from app.routers.projects import router as projects_router

app.include_router(projects_router)


from app.routers.auth import router as auth_router

app.include_router(auth_router)


from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=[
        "GET", "POST", "PUT", "PATCH", "DELETE"
    ],
    allow_headers=["*"],
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

from app.routers.me import router as me_router
app.include_router(me_router)
from app.routers.funding import router as funding_router
app.include_router(funding_router)
from app.routers.expenses import router as expenses_router
app.include_router(expenses_router)
from app.routers.documents import router as documents_router
app.include_router(documents_router)
from app.routers.extractions import router as extractions_router
app.include_router(extractions_router)
from app.routers.accountability import router as accountability_router
app.include_router(accountability_router)
from app.routers.transparency import router as transparency_router
app.include_router(transparency_router)


@app.middleware("http")
async def private_api_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response

from app.routers.github_progress import router as github_progress_router
app.include_router(github_progress_router)
from app.routers.roadmap import router as roadmap_router
app.include_router(roadmap_router)
from app.routers.roadmap_dependencies import router as roadmap_dependencies_router
app.include_router(roadmap_dependencies_router)
from app.routers.credibility import router as credibility_router
app.include_router(credibility_router)
from app.routers.progress import router as progress_router
app.include_router(progress_router)
