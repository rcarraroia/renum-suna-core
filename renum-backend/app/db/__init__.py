"""
Pacote de acesso a banco de dados para a Plataforma Renum.

Este pacote contém as implementações para acesso ao banco de dados PostgreSQL.
"""

from app.db.pg_pool import PostgreSQLPool, pg_pool

__all__ = ["PostgreSQLPool", "pg_pool"]