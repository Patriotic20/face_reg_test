from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.utils.dependencies import sync_permissions_to_db
from core.utils.base_roles import create_roles
from core.utils.assign_user_roles import setup_admin_user
from core.logging import logging
from core.db_helper import db_helper

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    
    try:
        # Sync permissions to database
        await sync_permissions_to_db()
        await create_roles()
        await setup_admin_user()
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await db_helper.dispose()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")