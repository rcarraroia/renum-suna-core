"""
Database initialization for the RAG module.

This module provides functions to initialize the database for the RAG module.
"""

from services.supabase import DBConnection
from knowledge_base.rag.utils.sql_scripts import (
    CREATE_TABLES_SQL,
    CREATE_FUNCTIONS_SQL,
    CREATE_RLS_POLICIES_SQL
)
from knowledge_base.rag.utils.agent_integration_sql import AGENT_INTEGRATION_SQL
from utils.logger import logger


async def initialize_database():
    """Initialize the database for the RAG module."""
    db = DBConnection()
    client = await db.client
    
    try:
        # Create tables
        logger.info("Creating RAG tables...")
        await client.execute(CREATE_TABLES_SQL)
        logger.info("RAG tables created successfully.")
        
        # Create functions
        logger.info("Creating RAG functions...")
        await client.execute(CREATE_FUNCTIONS_SQL)
        logger.info("RAG functions created successfully.")
        
        # Create RLS policies
        logger.info("Creating RAG RLS policies...")
        await client.execute(CREATE_RLS_POLICIES_SQL)
        logger.info("RAG RLS policies created successfully.")
        
        # Create agent integration functions
        logger.info("Creating agent integration functions...")
        await client.execute(AGENT_INTEGRATION_SQL)
        logger.info("Agent integration functions created successfully.")
        
        logger.info("RAG database initialization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Error initializing RAG database: {str(e)}")
        return False