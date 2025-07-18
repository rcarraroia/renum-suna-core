"""
Database module for the Renum backend.

This module provides database functionality for the Renum backend.
"""

from typing import Optional
import asyncio
from supabase import create_client, Client

from app.core.config import get_settings
from app.core.logger import logger


# Global database client
_db_client: Optional[Client] = None
_db_lock = asyncio.Lock()


async def initialize_db() -> Client:
    """Initialize the database client.
    
    Returns:
        Database client.
    """
    global _db_client
    
    if _db_client is not None:
        return _db_client
    
    async with _db_lock:
        if _db_client is not None:
            return _db_client
        
        settings = get_settings()
        
        try:
            logger.info("Initializing database client")
            _db_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Database client initialized successfully")
            return _db_client
        except Exception as e:
            logger.error(f"Error initializing database client: {str(e)}")
            raise


async def get_db_client() -> Client:
    """Get the database client.
    
    Returns:
        Database client.
    """
    global _db_client
    
    if _db_client is None:
        return await initialize_db()
    
    return _db_client


async def close_db() -> None:
    """Close the database client."""
    global _db_client
    
    if _db_client is not None:
        logger.info("Closing database client")
        _db_client = None