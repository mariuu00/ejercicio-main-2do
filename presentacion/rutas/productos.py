"""Capa 3 — Presentación: rutas HTTP y plantillas.

Las rutas no saben SQL ni reglas de negocio. Reciben la conexión, se la pasan
al servicio de `dominio/` y traducen el resultado a una plantilla.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from dominio import servicios
from dominio.esquemas import ProductoActualizar
from dominio.servicios import ProductoDuplicado
from nucleo.conexion import ConnectionDep

router = APIRouter(tags=["productos"])

# Este archivo vive en presentacion/rutas/, así que las plantillas están
# un nivel arriba, en presentacion/templates/.
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


def _no_encontrado(request: Request, producto_id: int):
    """Respuesta compartida cuando el producto no existe."""
    return templates.TemplateResponse(
        request=request,
        name="componentes/producto_no_encontrado.html",
        context={"producto_id": producto_id},
    )


@router.get("/productos")
async def listar_productos(request: Request, conn: ConnectionDep):
    # Ya implementado: muestra la página con la lista de productos.
    productos = await servicios.listar_productos(conn)
    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"productos": productos},
    )


@router.get("/productos/{producto_id}/editar")
async def editar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    producto = await servicios.obtener_producto(conn, producto_id)
    if producto is None:
        return _no_encontrado(request, producto_id)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_editar.html",
        context={
            "producto": producto,
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "cantidad": producto["cantidad"],
            "descripcion": producto["descripcion"],
            "errores": {},
        },
    )


@router.get("/productos/{producto_id}/cancelar")
async def cancelar_edicion_vista(request: Request, conn: ConnectionDep, producto_id: int):
    # Cancelar solo vuelve a mostrar la fila original, sin modificar nada.
    producto = await servicios.obtener_producto(conn, producto_id)
    if producto is None:
        return _no_encontrado(request, producto_id)
    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_producto.html",
        context={"producto": producto},
    )


@router.post("/productos/{producto_id}")
async def guardar_producto_vista(
    request: Request,
    conn: ConnectionDep,
    producto_id: int,
    nombre: Annotated[str, Form()] = "",
    precio: Annotated[str, Form()] = "",
    cantidad: Annotated[str, Form()] = "",
    descripcion: Annotated[str | None, Form()] = None,
):
    # El corazón del ejercicio. Pasos a seguir:
    # 1. Convierte precio y cantidad a número (float / int).
    # 2. Valida los datos con el esquema ProductoActualizar.
    # 3. Si hay errores, vuelve a mostrar el formulario con los valores
    #    que el usuario escribió y los mensajes de error (HTTP 422).
    # 4. Si los datos son válidos, delegás el guardado en el servicio.
    producto = await servicios.obtener_producto(conn, producto_id)
    if producto is None:
        return _no_encontrado(request, producto_id)

    errores = {}

    try:
        precio_validado = float(precio)
    except (TypeError, ValueError):
        precio_validado = precio
        errores["precio"] = "El precio debe ser un número válido."

    try:
        cantidad_validada = int(cantidad)
    except (TypeError, ValueError):
        cantidad_validada = cantidad
        errores["cantidad"] = "La cantidad debe ser un número entero válido."

    producto_validado = None
    try:
        producto_validado = ProductoActualizar(
            nombre=nombre,
            precio=precio_validado,
            cantidad=cantidad_validada,
            descripcion=descripcion,
        )
    except ValidationError as exc:
        for error in exc.errors():
            campo = error["loc"][0]
            errores.setdefault(campo, error["msg"])

    if errores:
        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            context={
                "producto": producto,
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    # El servicio aplica la regla de nombres duplicados: si la viola, lanza
    # ProductoDuplicado y la base de datos queda intacta. Acá solo se traduce
    # esa excepción a un mensaje junto al campo correspondiente.
    try:
        producto_actualizado = await servicios.guardar_producto(
            conn,
            producto_id,
            producto_validado.nombre,
            producto_validado.precio,
            producto_validado.cantidad,
            producto_validado.descripcion,
        )
    except ProductoDuplicado:
        errores["nombre"] = "Ya existe otro producto con ese nombre."
        return templates.TemplateResponse(
            request=request,
            name="componentes/fila_editar.html",
            context={
                "producto": producto,
                "nombre": nombre,
                "precio": precio,
                "cantidad": cantidad,
                "descripcion": descripcion,
                "errores": errores,
            },
            status_code=422,
        )

    return templates.TemplateResponse(
        request=request,
        name="componentes/fila_actualizada.html",
        context={"producto": producto_actualizado},
    )


@router.delete("/productos/{producto_id}")
async def eliminar_producto_vista(request: Request, conn: ConnectionDep, producto_id: int):
    await servicios.eliminar_producto(conn, producto_id)
    productos = await servicios.listar_productos(conn)
    return templates.TemplateResponse(
        request=request,
        name="productos.html",
        context={"productos": productos},
    )
