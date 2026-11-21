"""Modelos Pydantic para validación y serialización de libros."""

from pydantic import BaseModel, Field


class LibroBase(BaseModel):
    """Campos compartidos para la creación y reemplazo de un libro."""

    titulo: str = Field(..., min_length=3, max_length=100)
    autor: str = Field(..., min_length=3, max_length=60)
    anio: int = Field(..., ge=1000, le=2100)
    disponible: bool = True


class LibroCrear(LibroBase):
    """Esquema de entrada para POST /libros."""


class LibroActualizar(LibroBase):
    """Esquema de entrada para PUT /libros/{id}."""


class LibroParcial(BaseModel):
    """Esquema de entrada para PATCH /libros/{id}."""

    titulo: str | None = Field(default=None, min_length=3, max_length=100)
    autor: str | None = Field(default=None, min_length=3, max_length=60)
    anio: int | None = Field(default=None, ge=1000, le=2100)
    disponible: bool | None = None


class Libro(LibroBase):
    """Esquema de salida con el identificador asignado."""

    id: int