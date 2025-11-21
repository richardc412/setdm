import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.auth import auth_router
from app.features.example import example_router
from app.integration.unipile import unipile_router
from app.features.chats.router import router as chats_router
from app.db.base import init_db, AsyncSessionLocal
from app.services.message_sync import sync_all_chat_messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Initializes database and syncs messages on startup.
    """
    # Startup
    logger.info("Starting up application...")
    
    try:
        # Initialize database tables
        logger.info("Initializing database tables...")
        await init_db()
        logger.info("Database tables initialized successfully")
        
        # Sync messages from Unipile on startup
        logger.info("Starting message sync from Unipile...")
        async with AsyncSessionLocal() as db:
            try:
                stats = await sync_all_chat_messages(db, full_sync=False)
                logger.info(f"Message sync completed successfully: {stats}")
            except Exception as e:
                logger.error(f"Failed to sync messages on startup: {str(e)}")
                logger.warning("Application will continue, but messages may not be up to date")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(title="SetDM API", lifespan=lifespan)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(example_router)
app.include_router(unipile_router)
app.include_router(chats_router)


@app.get("/health")
def health():
    return {
        "ok": True,
    }
