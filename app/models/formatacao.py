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


def estilo_qualidade(qualidade: str) -> str:
    """Retorna uma folha de estilo CSS-like pronta pra QLabel.setStyleSheet(...):
    verde para 'Normal', amarelo para 'Circuito aberto', vermelho para qualquer
    outro estado (ex.: 'Fora da faixa')."""
    if qualidade == "Normal":
        cor = "#2e7d32"
    elif qualidade == "Circuito aberto":
        cor = "#f9a825"
    else:
        cor = "#c62828"
    return f"color: {cor}; font-weight: bold;"


def texto_status_conexao(conectado: bool) -> str:
    """Retorna 'Conectado' ou 'Desconectado' — status simulado do painel de recepção."""
    return "Conectado" if conectado else "Desconectado"


def estilo_status_conexao(conectado: bool) -> str:
    """Retorna estilo CSS pronto pra QLabel.setStyleSheet(...): verde quando
    conectado, cinza neutro quando desconectado (não é um estado de alarme)."""
    cor = "#2e7d32" if conectado else "#6b7280"
    return f"color: {cor}; font-weight: bold;"
