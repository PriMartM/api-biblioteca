"""Punto de entrada principal de la API REST de Biblioteca."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response, status

from datos import RepositorioLibros
from schemas import Libro, LibroActualizar, LibroCrear, LibroParcial

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API de la Biblioteca")
repo = RepositorioLibros()


def _buscar_indice_por_id(libro_id: int) -> int:
    """Devuelve el índice en la lista para un ID dado o lanza 404."""
    for indice, libro in enumerate(repo.libros):
        if libro["id"] == libro_id:
            return indice
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Libro con id {libro_id} no encontrado",
    )


@app.get("/", summary="Bienvenida de la API")
def raiz() -> dict[str, str]:
    """Devuelve el mensaje de estado inicial de la API."""
    return {"mensaje": "API de la biblioteca"}


@app.get("/libros", response_model=list[Libro], summary="Listar libros con filtros y paginación")
def listar_libros(
    autor: str | None = None,
    disponible: bool | None = None,
    desde: int = Query(default=0, ge=0),
    limite: int = Query(default=100, ge=1),
) -> list[dict[str, Any]]:
    """Lista libros aplicando filtros, orden ascendente por ID y paginación."""
    resultado = repo.libros

    if autor is not None:
        autor_normalizado = autor.lower()
        resultado = [
            libro for libro in resultado if libro["autor"].lower() == autor_normalizado
        ]

    if disponible is not None:
        resultado = [
            libro for libro in resultado if libro["disponible"] is disponible
        ]

    resultado_ordenado = sorted(resultado, key=lambda item: item["id"])
    return resultado_ordenado[desde : desde + limite]


@app.get("/libros/buscar", response_model=list[Libro], summary="Buscar libros por texto")
def buscar_libros(texto: str) -> list[dict[str, Any]]:
    """Busca coincidencias parciales en título o autor sin distinguir mayúsculas."""
    termino = texto.lower()
    coincidencias = [
        libro
        for libro in repo.libros
        if termino in libro["titulo"].lower() or termino in libro["autor"].lower()
    ]
    return sorted(coincidencias, key=lambda item: item["id"])


@app.get("/libros/estadisticas", summary="Obtener estadísticas de la biblioteca")
def obtener_estadisticas() -> dict[str, int]:
    """Calcula el total de libros, disponibles y prestados."""
    total = len(repo.libros)
    disponibles = sum(1 for libro in repo.libros if libro["disponible"])
    prestados = total - disponibles
    return {
        "total": total,
        "disponibles": disponibles,
        "prestados": prestados,
    }


@app.post(
    "/libros",
    response_model=Libro,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo libro",
)
def crear_libro(datos_libro: LibroCrear) -> dict[str, Any]:
    """Crea un libro nuevo verificando que no exista duplicado de título y autor."""
    titulo_norm = datos_libro.titulo.lower()
    autor_norm = datos_libro.autor.lower()

    for existente in repo.libros:
        if (
            existente["titulo"].lower() == titulo_norm
            and existente["autor"].lower() == autor_norm
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un libro con el mismo título y autor",
            )

    nuevo_libro: dict[str, Any] = {
        "id": repo.obtener_siguiente_id(),
        "titulo": datos_libro.titulo,
        "autor": datos_libro.autor,
        "anio": datos_libro.anio,
        "disponible": datos_libro.disponible,
    }
    repo.libros.append(nuevo_libro)
    repo.guardar()
    logger.info("Libro creado con id %d.", nuevo_libro["id"])
    return nuevo_libro


@app.get("/libros/{id}", response_model=Libro, summary="Obtener un libro por ID")
def obtener_libro(id: int) -> dict[str, Any]:
    """Devuelve los datos de un libro específico según su ID."""
    indice = _buscar_indice_por_id(id)
    return repo.libros[indice]


@app.put("/libros/{id}", response_model=Libro, summary="Reemplazar un libro completo")
def reemplazar_libro(id: int, datos_libro: LibroActualizar) -> dict[str, Any]:
    """Reemplaza todos los campos de un libro existente conservando su ID."""
    indice = _buscar_indice_por_id(id)
    libro_reemplazado: dict[str, Any] = {
        "id": id,
        "titulo": datos_libro.titulo,
        "autor": datos_libro.autor,
        "anio": datos_libro.anio,
        "disponible": datos_libro.disponible,
    }
    repo.libros[indice] = libro_reemplazado
    repo.guardar()
    logger.info("Libro con id %d reemplazado.", id)
    return libro_reemplazado


@app.patch("/libros/{id}", response_model=Libro, summary="Actualizar parcialmente un libro")
def actualizar_libro(id: int, datos_parciales: LibroParcial) -> dict[str, Any]:
    """Actualiza únicamente los campos enviados en la petición."""
    indice = _buscar_indice_por_id(id)
    cambios = datos_parciales.model_dump(exclude_unset=True)

    if cambios:
        repo.libros[indice].update(cambios)
        repo.guardar()
        logger.info("Libro con id %d actualizado parcialmente.", id)

    return repo.libros[indice]


@app.delete(
    "/libros/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un libro",
)
def eliminar_libro(id: int) -> Response:
    """Elimina un libro existente y devuelve respuesta vacía 204."""
    indice = _buscar_indice_por_id(id)
    repo.libros.pop(indice)
    repo.guardar()
    logger.info("Libro con id %d eliminado.", id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/libros/{id}/prestar", response_model=Libro, summary="Prestar un libro")
def prestar_libro(id: int) -> dict[str, Any]:
    """Marca un libro disponible como prestado (disponible = False)."""
    indice = _buscar_indice_por_id(id)
    libro = repo.libros[indice]
    if not libro["disponible"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El libro ya se encuentra prestado",
        )
    libro["disponible"] = False
    repo.guardar()
    logger.info("Libro con id %d prestado.", id)
    return libro


@app.post("/libros/{id}/devolver", response_model=Libro, summary="Devolver un libro")
def devolver_libro(id: int) -> dict[str, Any]:
    """Marca un libro prestado como disponible (disponible = True)."""
    indice = _buscar_indice_por_id(id)
    libro = repo.libros[indice]
    if libro["disponible"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El libro ya se encuentra disponible",
        )
    libro["disponible"] = True
    repo.guardar()
    logger.info("Libro con id %d devuelto.", id)
    return libro