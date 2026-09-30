# Ejercicio: edición de productos (proyecto base)

Proyecto de partida del ejercicio **"Edición de registros con FastAPI, Jinja2, HTMX y PostgreSQL"**.

El enunciado completo está en [`Docs/ejercicio_edicion_productos.md`](Docs/ejercicio_edicion_productos.md).

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

```bash
cp .env.example .env
```

Edita `.env` y define la cadena de conexión a tu base de datos PostgreSQL.

## Ejecución

```bash
uvicorn main:app --reload
```

Abre el navegador en <http://127.0.0.1:8000/productos>.

## Estado del proyecto

- La página `GET /productos` ya muestra la lista de productos.
- El botón **Editar** apunta a las rutas que debes implementar.
- Los archivos `dominio/esquemas.py`, `dominio/repositorios.py` y
  `presentacion/rutas/productos.py` contienen comentarios `TODO(n)` que
  indican qué falta en cada paso.
- La carpeta `solucion/` contiene la implementación completa de referencia.

## Estructura del proyecto

El código está repartido en **tres capas**. Cada una solo conoce las que están
por debajo de ella: las dependencias apuntan hacia adentro, nunca hacia arriba.

```
ejercicio/
├── main.py                 ← solo arma las piezas
├── nucleo/                 ← CAPA 1 · CONEXIÓN
│   ├── configuracion.py    ← lee DATABASE_URL
│   └── conexion.py         ← pool + la dependencia que lo expone
│
├── dominio/                ← CAPA 2 · LÓGICA
│   ├── esquemas.py         ← validación (Pydantic)
│   ├── servicios.py        ← reglas del negocio
│   └── repositorios.py     ← el único archivo con SQL
│
├── presentacion/           ← CAPA 3 · DISEÑO
│   ├── rutas/productos.py  ← rutas HTTP
│   ├── templates/          ← plantillas Jinja2
│   └── static/             ← CSS e imágenes
│
├── Docs/
├── tests/                  ← opcional
├── requirements.txt
└── vercel.json
```

### Qué hace cada capa

| Capa | Carpeta | Responsabilidad | No sabe |
| ---- | ------- | --------------- | ------- |
| 1 | `nucleo/` | Leer el entorno y hablar con PostgreSQL. | Qué es un producto. |
| 2 | `dominio/` | Qué puede hacer el catálogo y con qué reglas. | Que existen rutas HTTP o plantillas. |
| 3 | `presentacion/` | Traducir peticiones HTTP en llamadas al dominio y resultados en HTML. | Cómo se guarda un producto. |
| — | `main.py` | Conectar las tres capas y nada más. | Cualquier regla. |

### Reglas de imports

1. `presentacion/` puede importar de `dominio/` y de `nucleo/`.
2. `dominio/` puede importar de `nucleo/`, pero nunca de `presentacion/`.
3. `nucleo/` no importa de ninguna otra capa.
4. `presentacion/` **nunca** importa `dominio.repositorios` directamente: si
   necesita datos, se los pide a `dominio.servicios`.

### La regla de negocio

`servicios.guardar_producto()` es el único lugar donde se comprueba que **no
se repitan nombres entre productos distintos**. Si se repite, lanza
`ProductoDuplicado` y no modifica nada; la ruta traduce esa excepción en un
mensaje de error. La tabla no tiene restricción `UNIQUE` sobre `nombre`, así
que la comparación se hace en Python e ignora mayúsculas y espacios.

### Prueba de fuego

```bash
# El SQL solo puede aparecer en un archivo:
grep -rniE "select |insert |update |delete " --include=*.py nucleo dominio presentacion main.py

# presentacion/ no debe conocer los repositorios:
grep -rn "repositorios" presentacion/

# Ninguna capa inferior puede mirar hacia arriba:
grep -rn "presentacion" nucleo dominio
```

Si alguna de las tres búsquedas devuelve algo inesperado, hay una capa
metida donde no corresponde.
