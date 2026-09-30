"""Capa 2 — Acceso a datos: el único archivo del proyecto con SQL.

Todas las consultas usan parámetros ($1, $2, ...): nunca se concatenan valores
recibidos del formulario dentro del texto SQL. Estas funciones no deciden nada,
solo preguntan y devuelven filas; las reglas viven en `dominio/servicios.py`.
"""

import asyncpg


async def obtener_productos(conn: asyncpg.Connection) -> list[dict]:
    """Devuelve todos los productos, ordenados por nombre."""
    # TODO(2): escribe la consulta SELECT y convierte las filas a dicts.
    filas = await conn.fetch(
        """
        SELECT id, nombre, precio, cantidad, descripcion
        FROM productos
        ORDER BY nombre
        """
    )
    return [dict(fila) for fila in filas]


async def obtener_producto(conn: asyncpg.Connection, producto_id: int) -> dict | None:
    """Busca un producto por su clave primaria (id)."""
    # TODO(3): escribe la consulta SELECT con el parámetro $1.
    fila = await conn.fetchrow(
        """
        SELECT id, nombre, precio, cantidad, descripcion
        FROM productos
        WHERE id = $1
        """,
        producto_id,
    )
    return dict(fila) if fila is not None else None


async def existe_producto_con_nombre(
    conn: asyncpg.Connection,
    nombre: str,
    excluir_id: int | None = None,
) -> bool:
    """¿Ya existe otro producto con ese nombre?

    La comparación ignora mayúsculas y espacios sobrantes, así que "  teclado "
    cuenta como el mismo nombre que "Teclado".

    `excluir_id` permite preguntar por un producto sin que choque consigo mismo:
    al editar, se pasa su propio id y solo se detectan los demás.
    """
    if excluir_id is None:
        return await conn.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM productos
                WHERE LOWER(BTRIM(nombre)) = LOWER(BTRIM($1))
            )
            """,
            nombre,
        )

    return await conn.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM productos
            WHERE LOWER(BTRIM(nombre)) = LOWER(BTRIM($1))
              AND id <> $2
        )
        """,
        nombre,
        excluir_id,
    )


async def actualizar_producto(
    conn: asyncpg.Connection,
    producto_id: int,
    nombre: str,
    precio: float,
    cantidad: int,
    descripcion: str | None,
) -> bool:
    """Actualiza un producto identificado por su clave primaria (id).

    Devuelve True si la consulta modificó una fila, False si no existía.
    """
    fila = await conn.execute(
        """
        UPDATE productos
        SET nombre = $2, precio = $3, cantidad = $4, descripcion = $5
        WHERE id = $1
        """,
        producto_id,
        nombre,
        precio,
        cantidad,
        descripcion,
    )
    return fila == "UPDATE 1"


async def eliminar_producto(conn: asyncpg.Connection, producto_id: int) -> bool:
    """Borra un producto por su clave primaria. Devuelve si había fila."""
    fila = await conn.execute(
        """
        DELETE FROM productos
        WHERE id = $1
        """,
        producto_id,
    )
    return fila == "DELETE 1"
