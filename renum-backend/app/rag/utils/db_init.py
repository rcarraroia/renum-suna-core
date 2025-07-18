"""
Database initialization for the RAG module.

This module provides functions to initialize the database for the RAG module.
"""

from app.core.database import get_db_client
from app.rag.utils.sql_scripts import INITIALIZE_DATABASE_SQL
from app.core.logger import logger


async def initialize_database():
    """Initialize the database for the RAG module."""
    client = await get_db_client()
    
    try:
        # Create tables, functions, and policies
        logger.info("Initializing RAG database...")
        await client.execute(INITIALIZE_DATABASE_SQL)
        logger.info("RAG database initialization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing RAG database: {str(e)}")
        return False