from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import get_db
from app.repositories.user_repo import UserRepository
from app.services.falkor_service import falkor_service
from app.routers import auth, sessions, analytics, admin, graph
import logging

# Setup standard logger
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="OmniHealth Graph: clinical documentation and coding with FalkorDB as the context, reasoning and memory layer",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,  # *.vercel.app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API V1 routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(graph.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Healthcare Platform Backend...")
    
    # 1. Seed MongoDB default users (doctor, coder, auditor, admin)
    try:
        db = get_db()
        user_repo = UserRepository(db)
        await user_repo.seed_default_users()
    except Exception as e:
        logger.error(f"Error seeding database users: {e}")
        
    # 2. Seed FalkorDB graphs (clinical_rules, hospital_brain, patient_P-9801)
    try:
        result = falkor_service.init_databases()
        logger.info(f"FalkorDB init: {result}")
    except Exception as e:
        logger.error(f"Error seeding FalkorDB: {e}")

    logger.info("System startup sequences completed successfully.")

@app.get("/health", tags=["Health Checks"])
async def health_check():
    graph = falkor_service.status()
    return {
        "status": "healthy" if graph["available"] else "degraded",
        "services": {
            "database": "online",
            "agents": "active",
            "graph_engine": "online" if graph["available"] else "offline",
            "graphs": graph["graphs"],
        },
    }
