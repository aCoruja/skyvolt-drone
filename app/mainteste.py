# Destino no GitHub (repo skyvolt-drone): app/main.py
from __future__ import annotations

import os
import sys

from PyQt5.QtWidgets import QApplication

from app.database.connection import Database
from app.models.logger_service import log_error, log_info
from app.controllers.main_controller import criar_janela_principal


def main() -> int:
    # 1. Inicializa o banco SQLite e valida o esquema relacional (Requisito Obrigatório A1/2)
    try:
        Database.init_db()
        # Formato exato exigido pelo edital no smartgrid.log
        log_info("Conexão com SQLite estabelecida e esquema validado.")
    except Exception as e:
        log_error(f"Erro fatal ao inicializar banco de dados SQLite: {e}")
        return 1

    # 2. Inicializa a aplicação Qt
    app = QApplication(sys.argv)

    # 3. Carregamento seguro da folha de estilos QSS (funciona em qualquer diretório)
    dir_atual = os.path.dirname(os.path.abspath(__file__))
    # Procura estilo.qss tanto em app/ui/ quanto em ui/
    caminhos_qss = [
        os.path.join(dir_atual, "ui", "estilo.qss"),
        os.path.join(dir_atual, "app", "ui", "estilo.qss"),
        os.path.join(dir_atual, "..", "app", "ui", "estilo.qss"),
    ]
    for qss_path in caminhos_qss:
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            break

    # 4. Cria e exibe a janela principal maximizada (mantendo o seu padrão)
    janela = criar_janela_principal()
    janela.showMaximized()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
