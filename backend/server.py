from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from fastapi import Depends

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.database import load_backend_environment, DatabaseSettings, create_database_client

load_backend_environment()

from utils.auth import require_roles
from utils.roles import UserRole

# Import routes
from routes.admin_auth import router as admin_auth_router
from routes.client_auth import router as client_auth_router
from routes.content import router as content_router
from routes.blog import router as blog_router
from routes.demo_requests import router as demo_router
from routes.clients import router as clients_router
from routes.client_dashboard import router as client_dashboard_router
from routes.uploads import router as uploads_router
from routes.password_reset import router as password_reset_router
from routes.notifications import router as notifications_router
from routes.architecture import router as architecture_router
from routes.seo import router as seo_router
from routes.projects import router as projects_router
from routes.activity import router as activity_router
from routes.assets import router as assets_router
from routes.security_runs import router as security_runs_router
from routes.missions import router as missions_router
from routes.findings import router as findings_router
from routes.remediations import router as remediations_router
from routes.domain_overview import router as domain_overview_router
from routes.github_integrations import router as github_integrations_router
from routes.github_webhooks import router as github_webhooks_router

# Database client
db_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    # Startup
    settings = DatabaseSettings.from_environment()
    db_client = create_database_client(settings)
    db = db_client[settings.database_name]
    app.state.db = db
    
    # Business data is never seeded on application startup. Run seed_db.py explicitly.
    try:
        print("[OK] HavoSec Backend started")
        yield
    finally:
        db_client.close()

app = FastAPI(
    title="HavoSec API",
    description="HavoSec Cybersecurity Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
allowed_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
allowed_origin_regex = os.environ.get("CORS_ORIGIN_REGEX", r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+):3000$")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(activity_router, prefix="/api/activity", tags=["Activity"])
app.include_router(assets_router, prefix="/api/assets", tags=["Assets"])
app.include_router(security_runs_router, prefix="/api/security-runs", tags=["Security Runs"])
app.include_router(missions_router, prefix="/api/missions", tags=["Missions"])
app.include_router(findings_router, prefix="/api/findings", tags=["Findings"])
app.include_router(remediations_router, prefix="/api/remediations", tags=["Remediations"])
app.include_router(domain_overview_router, prefix="/api/domain/overview", tags=["Domain Overview"])
app.include_router(github_integrations_router, prefix="/api/integrations/github", tags=["GitHub Integration"])
app.include_router(github_webhooks_router, prefix="/api/webhooks", tags=["GitHub Webhooks"])
admin_dependencies = [Depends(require_roles(UserRole.SUPERADMIN))]
app.include_router(admin_auth_router, prefix="/api/admin/auth", tags=["Admin Auth"])
app.include_router(content_router, prefix="/api/admin/content", tags=["Admin Content"], dependencies=admin_dependencies)
app.include_router(content_router, prefix="/api/content", tags=["Public Content"])
app.include_router(blog_router, prefix="/api/admin/blog", tags=["Admin Blog"], dependencies=admin_dependencies)
app.include_router(blog_router, prefix="/api/blog", tags=["Public Blog"])
app.include_router(demo_router, prefix="/api/admin/demo-requests", tags=["Admin Demo"], dependencies=admin_dependencies)
app.include_router(demo_router, prefix="/api/demo", tags=["Public Demo"])
app.include_router(demo_router, prefix="/api/book-demo", tags=["Book Demo"])
app.include_router(clients_router, prefix="/api/admin/clients", tags=["Admin Clients"], dependencies=admin_dependencies)
app.include_router(client_auth_router, prefix="/api/auth", tags=["Client Auth"])
app.include_router(client_dashboard_router, prefix="/api/dashboard", tags=["Client Dashboard"])
app.include_router(uploads_router, prefix="/api/uploads", tags=["File Uploads"])
app.include_router(password_reset_router, prefix="/api/auth", tags=["Password Reset & Verification"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(architecture_router, tags=["Architecture Maps"])
app.include_router(seo_router, prefix="/api/seo", tags=["SEO Management"])
app.include_router(seo_router, prefix="/api/admin/seo", tags=["Admin SEO Management"], dependencies=admin_dependencies)

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "service": "HavoSec API"}

@app.get("/api/admin/dashboard", dependencies=[Depends(require_roles(UserRole.SUPERADMIN))])
async def admin_dashboard():
    from routes.blog import get_blog_stats
    from routes.demo_requests import get_demo_stats
    from routes.clients import get_client_stats
    
    blog_stats = await get_blog_stats(app.state.db)
    demo_stats = await get_demo_stats(app.state.db)
    client_stats = await get_client_stats(app.state.db)
    
    return {
        "overview": {
            "blog": blog_stats,
            "demoRequests": demo_stats,
            "clients": client_stats
        }
    }
