"""Capa 1 — Conexión a PostgreSQL.

El pool de asyncpg y la dependencia de FastAPI que lo expone viven en el
mismo archivo porque nacen el uno del otro: la dependencia no abre conexiones,
solo pide una prestada al pool.
"""

from collections.abc import AsyncIterator
from typing import Annotated

import asyncpg
from fastapi import Depends


class GestorConexion:
    """Envoltorio mínimo sobre el pool de conexiones de asyncpg."""

    pool: asyncpg.Pool | None = None

    async def connect(self, database_url: str) -> None:
        # Crea un pool: varias conexiones que se reutilizan entre peticiones.
        self.pool = await asyncpg.create_pool(dsn=database_url)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


conexion = GestorConexion()


async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    """Dependencia de FastAPI: cede una conexión del pool a cada petición."""
    async with conexion.pool.acquire() as conn:
        yield conn


# Así las rutas reciben la conexión de la base de datos como parámetro.
ConnectionDep = Annotated[asyncpg.Connection, Depends(get_connection)]
