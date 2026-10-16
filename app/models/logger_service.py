from __future__ import annotations

import logging
import os
from app.database.connection import BASE_DIR

LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "smartgrid.log")

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("smartgrid")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Formatação padronizada: [TIMESTAMP] [SEVERIDADE] Descrição
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Gravador permanente em arquivo
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Gravador simultâneo no terminal/console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)


def log_info(mensagem: str) -> None:
    logger.info(mensagem)


def log_warning(mensagem: str) -> None:
    logger.warning(mensagem)


def log_error(mensagem: str) -> None:
    logger.error(mensagem)
