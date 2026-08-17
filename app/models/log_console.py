# Destino no GitHub (repo skyvolt-drone): app/models/log_console.py
from __future__ import annotations

from app import BOLD, CYAN, GREEN, RESET, WHITE, YELLOW

RED = "\033[38;5;196m"

_CORES_SEVERIDADE = {
    "Info": CYAN,
    "Alerta": YELLOW,
    "Critico": RED,
}


def log_evento(tipo: str, descricao: str, severidade: str) -> None:
    """Ecoa no console um evento do sistema, colorido conforme a severidade
    (mesma paleta ANSI do banner de abertura em app/__init__.py)."""
    cor = _CORES_SEVERIDADE.get(severidade, WHITE)
    print(f"{cor}{BOLD}[{severidade.upper()}]{RESET} {tipo}: {descricao}")


def log_sucesso(mensagem: str) -> None:
    """Linha de status verde, para marcos concluídos (ex.: janela montada)."""
    print(f"{GREEN}{BOLD}✓{RESET} {mensagem}")
