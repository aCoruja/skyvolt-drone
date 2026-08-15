# Destino no GitHub (repo skyvolt-drone): app/main.py
from __future__ import annotations

import sys

from PyQt5.QtWidgets import QApplication

from app.controllers.main_controller import MainController


def criar_janela_principal() -> MainController:
    return MainController()


def main() -> int:
    app = QApplication(sys.argv)
    # TODO: app.setStyleSheet(...) carregando app/ui/estilo.qss quando disponível (Moura)
    janela = criar_janela_principal()
    janela.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
