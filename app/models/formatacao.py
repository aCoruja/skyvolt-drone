from __future__ import annotations

# Todas as funções devolvem string com decimal em vírgula (padrão PT-BR).


def formatar_tensao(valor: float) -> str:
    """Retorna string 'xxx,x V'."""
    return f"{valor:.1f} V".replace(".", ",")


def formatar_corrente(valor: float) -> str:
    """Retorna string 'x,xx A'."""
    return f"{valor:.2f} A".replace(".", ",")


def formatar_potencia(valor_watts: float) -> str:
    """'xxx,x W' abaixo de 1000 W; 'x,xx kW' a partir de 1000 W."""
    if valor_watts < 1000:
        return f"{valor_watts:.1f} W".replace(".", ",")
    return f"{valor_watts / 1000:.2f} kW".replace(".", ",")


def texto_status_disjuntor(fechado: bool) -> str:
    """Retorna 'Fechado' ou 'Aberto'."""
    return "Fechado" if fechado else "Aberto"


def cor_status_disjuntor(fechado: bool) -> str:
    """Retorna cor (verde '#2e7d32') quando fechado, e outra (vermelho '#c62828') quando aberto."""
    return "#2e7d32" if fechado else "#c62828"


def estilo_status_disjuntor(fechado: bool) -> str:
    """Retorna uma folha de estilo CSS-like pronta pra QLabel.setStyleSheet(...),
    combinando cor_status_disjuntor()."""
    return f"color: {cor_status_disjuntor(fechado)}; font-weight: bold;"
