from __future__ import annotations

# Stub — assinaturas travadas (Trello #12, responsável: Vitoria).
# Todas as funções devem devolver string com decimal em vírgula (padrão PT-BR).


def formatar_tensao(valor: float) -> str:
    """TODO(Vitoria): retorna string 'xxx,x V'."""
    raise NotImplementedError


def formatar_corrente(valor: float) -> str:
    """TODO(Vitoria): retorna string 'x,xx A'."""
    raise NotImplementedError


def formatar_potencia(valor_watts: float) -> str:
    """TODO(Vitoria): 'xxx,x W' abaixo de 1000 W; 'x,xx kW' a partir de 1000 W."""
    raise NotImplementedError


def texto_status_disjuntor(fechado: bool) -> str:
    """TODO(Vitoria): retorna 'Fechado' ou 'Aberto'."""
    raise NotImplementedError


def cor_status_disjuntor(fechado: bool) -> str:
    """TODO(Vitoria): retorna cor (ex.: '#2e7d32' verde) quando fechado,
    e outra (ex.: '#c62828' vermelho) quando aberto."""
    raise NotImplementedError


def estilo_status_disjuntor(fechado: bool) -> str:
    """TODO(Vitoria): retorna uma folha de estilo CSS-like pronta pra
    QLabel.setStyleSheet(...), combinando cor_status_disjuntor() (ex.:
    f'color: {cor_status_disjuntor(fechado)}; font-weight: bold;')."""
    raise NotImplementedError
