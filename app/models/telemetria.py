# Destino no GitHub (repo skyvolt-drone): app/models/telemetria.py
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime

from app.models.configuracao import ConfiguracaoSistema


@dataclass
class LeituraTelemetria:
    timestamp: datetime
    tensao: float
    corrente: float
    disjuntor_fechado: bool


def ler_telemetria(
    tensao_nominal: float = 220.0,
    corrente_base: float = 5.0,
    disjuntor_fechado: bool = True,
) -> LeituraTelemetria:
    """Simula a leitura de tensão/corrente do quadro elétrico.

    Na Unidade 4 esta função é substituída pela leitura via porta serial,
    mantendo o mesmo retorno (LeituraTelemetria).
    """
    variacao = random.uniform(-0.03, 0.03)
    tensao = round(tensao_nominal * (1 + variacao), 1)
    corrente = (
        round(max(0.0, random.gauss(corrente_base, 1.2)), 2) if disjuntor_fechado else 0.0
    )
    return LeituraTelemetria(
        timestamp=datetime.now(),
        tensao=tensao,
        corrente=corrente,
        disjuntor_fechado=disjuntor_fechado,
    )


def calcular_potencia(leitura: LeituraTelemetria) -> float:
    """P = V × I. Retorna 0 quando o disjuntor está aberto."""
    if not leitura.disjuntor_fechado:
        return 0.0
    return leitura.tensao * leitura.corrente


def corrente_excedida(leitura: LeituraTelemetria, configuracao: ConfiguracaoSistema) -> bool:
    return leitura.corrente > configuracao.corrente_maxima


def avaliar_qualidade(leitura: LeituraTelemetria, configuracao: ConfiguracaoSistema) -> str:
    """Classifica a leitura como 'Normal' ou 'Fora da faixa' conforme os limites de `configuracao`."""
    tensao_ok = configuracao.tensao_minima <= leitura.tensao <= configuracao.tensao_maxima
    if not tensao_ok or corrente_excedida(leitura, configuracao):
        return "Fora da faixa"
    return "Normal"
