from __future__ import annotations

import math
import random


def gerar_curva_consumo(pontos: int = 24) -> tuple[list[float], list[float], list[float]]:
    """Gera (horas, tensoes, correntes) para alimentar o gráfico de consumo.

    Tensão oscilando +-3% em torno de 220 V; corrente com perfil de carga
    (pico entre 18h e 21h).
    """
    horas: list[float] = []
    tensoes: list[float] = []
    correntes: list[float] = []

    for i in range(pontos):
        hora = i * (24 / pontos)
        horas.append(hora)

        # tensão oscilando +-3% em torno de 220 V
        variacao_tensao = random.uniform(-0.03, 0.03)
        tensoes.append(220 * (1 + variacao_tensao))

        # perfil de carga: base baixa + pico gaussiano entre 18h e 21h (centro ~19,5h)
        corrente_base = 3.0 + 1.0 * math.sin(math.pi * hora / 24)
        pico = 6.0 * math.exp(-((hora - 19.5) ** 2) / (2 * 1.5 ** 2))
        ruido = random.uniform(-0.15, 0.15)
        correntes.append(max(0.0, corrente_base + pico + ruido))

    return horas, tensoes, correntes


def potencias_da_curva(tensoes: list[float], correntes: list[float]) -> list[float]:
    """Calcula a potência (P = V × I) ponto a ponto a partir das listas
    retornadas por gerar_curva_consumo().
    """
    return [v * i for v, i in zip(tensoes, correntes)]
