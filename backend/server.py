from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

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

# Database client
db_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    # Startup
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "havosec")
    db_client = AsyncIOMotorClient(mongo_url)
    db = db_client[db_name]
    app.state.db = db
    
    # Seed database
    from utils.seed import seed_database
    await seed_database(db)
    
    print("✓ HavoSec Backend started")
    yield
    # Shutdown
    db_client.close()

app = FastAPI(
    title="HavoSec API",
    description="HavoSec Cybersecurity Platform Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_auth_router, prefix="/api/admin/auth", tags=["Admin Auth"])
app.include_router(content_router, prefix="/api/admin/content", tags=["Admin Content"])
app.include_router(content_router, prefix="/api/content", tags=["Public Content"])
app.include_router(blog_router, prefix="/api/admin/blog", tags=["Admin Blog"])
app.include_router(blog_router, prefix="/api/blog", tags=["Public Blog"])
app.include_router(demo_router, prefix="/api/admin/demo-requests", tags=["Admin Demo"])
app.include_router(demo_router, prefix="/api/demo", tags=["Public Demo"])
app.include_router(demo_router, prefix="/api/book-demo", tags=["Book Demo"])
app.include_router(clients_router, prefix="/api/admin/clients", tags=["Admin Clients"])
app.include_router(client_auth_router, prefix="/api/auth", tags=["Client Auth"])
app.include_router(client_dashboard_router, prefix="/api/dashboard", tags=["Client Dashboard"])
app.include_router(uploads_router, prefix="/api/uploads", tags=["File Uploads"])

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "service": "HavoSec API"}

@app.get("/api/admin/dashboard")
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
