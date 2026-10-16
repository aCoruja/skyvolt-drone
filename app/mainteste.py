from __future__ import annotations

import os
import sys

# Garante que a pasta raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication

from app.database.connection import Database
from app.models.logger_service import log_error, log_info
from app.controllers.main_controller import criar_janela_principal


def main() -> None:
    # 1. Inicializa o banco de dados e valida o esquema
    try:
        Database.init_db()
        # Formato exato solicitado no edital:
        log_info("Conexão com SQLite estabelecida e esquema validado.")
    except Exception as e:
        log_error(f"Erro fatal ao inicializar banco de dados SQLite: {e}")
        sys.exit(1)

    # 2. Inicialização da aplicação Qt
    app = QApplication(sys.argv)

    # 3. Carregamento da folha de estilos QSS se existir
    qss_path = os.path.join(os.path.dirname(__file__), "app", "ui", "estilo.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # 4. Cria e exibe a janela principal
    janela = criar_janela_principal()
    janela.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
