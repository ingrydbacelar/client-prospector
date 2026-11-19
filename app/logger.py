"""
Configuração centralizada de logging.

Gera logs tanto no console quanto em arquivo (logs/app.log), com rotação
simples por tamanho para não crescer indefinidamente.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger configurado com handlers de console e arquivo.

    Args:
        name: Nome do logger (geralmente __name__ do módulo chamador).

    Returns:
        Instância de logging.Logger pronta para uso.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Evita duplicar handlers caso get_logger seja chamado mais de uma vez
        # para o mesmo nome de módulo.
        return logger

    logger.setLevel(settings.log_level.upper())

    formatter = logging.Formatter(_LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
