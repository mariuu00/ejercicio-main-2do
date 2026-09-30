from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from nucleo.configuracion import cargar_configuracion
from nucleo.conexion import conexion
from presentacion.rutas.productos import router

PRESENTACION = Path(__file__).parent / "presentacion"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar la aplicación se crea el pool de conexiones a PostgreSQL.
    await conexion.connect(cargar_configuracion().database_url)
    yield
    # Al apagar la aplicación, el pool se cierra para liberar las conexiones.
    await conexion.close()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=PRESENTACION / "static"), name="static")

app.include_router(router)
