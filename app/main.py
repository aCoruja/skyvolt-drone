from __future__ import annotations

import os
import sqlite3
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from app.controllers.main_controller import criar_janela_principal
from app.database.connection import Database
from app.models.logger_service import log_error, log_info

ESTILO_QSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "estilo.qss")


def main() -> int:
    app = QApplication(sys.argv)

    try:
        Database.init_db()
    except sqlite3.Error as erro:
        log_error(f"Falha ao inicializar o banco SQLite: {erro}.")
        QMessageBox.critical(None, "SkyVolt", f"Não foi possível abrir o banco de dados:\n{erro}")
        return 1
    log_info("Conexão com SQLite estabelecida e esquema validado.")

    try:
        with open(ESTILO_QSS, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except OSError as erro:
        log_error(f"Arquivo de estilo não carregado: {erro}.")

    janela = criar_janela_principal()
    janela.showMaximized()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
