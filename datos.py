"""Gestión de persistencia en JSON y estado en memoria de los libros."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RUTA_DATOS = Path(__file__).parent / "datos" / "libros.json"


class RepositorioLibros:
    """Administra el almacenamiento, lectura y generación de IDs de libros."""

    def __init__(self, ruta: Path = RUTA_DATOS) -> None:
        self.ruta = ruta
        self.libros: list[dict[str, Any]] = []
        self.proximo_id: int = 1
        self.cargar()

    def cargar(self) -> None:
        """Carga los libros desde el archivo JSON con tolerancia a fallos."""
        if not self.ruta.exists():
            logger.info("Archivo %s no encontrado. Iniciando lista vacía.", self.ruta)
            self.libros = []
            self.proximo_id = 1
            return

        try:
            contenido = self.ruta.read_text(encoding="utf-8").strip()
            if not contenido:
                logger.warning("Archivo %s vacío. Iniciando lista vacía.", self.ruta)
                self.libros = []
                self.proximo_id = 1
                return

            datos = json.loads(contenido)
            if not isinstance(datos, list):
                logger.warning("Formato inválido en %s. Iniciando lista vacía.", self.ruta)
                self.libros = []
                self.proximo_id = 1
                return

            self.libros = sorted(datos, key=lambda item: item["id"])
            if self.libros:
                max_id = max(item["id"] for item in self.libros)
                self.proximo_id = max_id + 1
            else:
                self.proximo_id = 1
            logger.info("Se cargaron %d libros desde %s.", len(self.libros), self.ruta)
        except (json.JSONDecodeError, KeyError, TypeError, OSError) as exc:
            logger.error("Error al leer %s (%s). Iniciando lista vacía.", self.ruta, exc)
            self.libros = []
            self.proximo_id = 1

    def guardar(self) -> None:
        """Persiste la lista actual de libros ordenada por ID en el archivo JSON."""
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        libros_ordenados = sorted(self.libros, key=lambda item: item["id"])
        self.ruta.write_text(
            json.dumps(libros_ordenados, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Datos guardados correctamente en %s.", self.ruta)

    def obtener_siguiente_id(self) -> int:
        """Devuelve el próximo ID disponible e incrementa el contador interno."""
        actual = self.proximo_id
        self.proximo_id += 1
        return actual