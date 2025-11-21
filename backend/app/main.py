import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.features.auth import auth_router
from app.features.example import example_router
from app.integration.unipile import unipile_router
from app.features.chats.router import router as chats_router
from app.features.webhooks import webhook_router
from app.db.base import init_db, AsyncSessionLocal
from app.services.message_sync import sync_all_chat_messages
from app.services.pending_message_processor import process_pending_messages
from app.services.webhook_manager import ensure_webhook_exists

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
    Initializes database, syncs messages on startup, and starts background scheduler.
    """
    # Startup
    logger.info("Starting up application...")
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler()
    
    try:
        # Initialize database tables
        logger.info("Initializing database tables...")
        await init_db()
        logger.info("Database tables initialized successfully")
        
        # Ensure webhook exists in Unipile for real-time message ingestion
        logger.info("Ensuring webhook exists in Unipile...")
        try:
            webhook_id = await ensure_webhook_exists()
            if webhook_id:
                logger.info(f"Webhook ready: ID={webhook_id}")
            else:
                logger.warning("Webhook not configured - real-time message ingestion disabled")
        except Exception as e:
            logger.error(f"Failed to setup webhook: {str(e)}")
            logger.warning("Application will continue without real-time webhook support")
        
        # Sync messages from Unipile on startup
        logger.info("Starting message sync from Unipile...")
        async with AsyncSessionLocal() as db:
            try:
                stats = await sync_all_chat_messages(db, full_sync=False)
                logger.info(f"Message sync completed successfully: {stats}")
            except Exception as e:
                logger.error(f"Failed to sync messages on startup: {str(e)}")
                logger.warning("Application will continue, but messages may not be up to date")
        
        # Start background scheduler for pending message processing
        logger.info("Starting background scheduler for pending message processing...")
        scheduler.add_job(
            process_pending_messages,
            trigger=IntervalTrigger(seconds=10),
            id="pending_message_processor",
            name="Process pending messages every 10 seconds",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Background scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    scheduler.shutdown()
    logger.info("Background scheduler stopped")


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
app.include_router(webhook_router)


@app.get("/health")
def health():
    return {
        "ok": True,
    }
