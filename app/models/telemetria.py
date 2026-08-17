# Destino no GitHub (repo skyvolt-drone): app/models/telemetria.py
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime

from app.models.configuracao import ConfiguracaoSistema

TIPOS_SINAL_DISPONIVEIS = ["AC", "DC"]
TENSAO_NOMINAL_AC = 220.0  # V — circuito residencial padrão
TENSAO_NOMINAL_DC = 12.0  # V — fonte/bateria baixa tensão (sempre <=100V, RNF06)


@dataclass
class LeituraTelemetria:
    timestamp: datetime
    tensao: float
    corrente: float
    disjuntor_fechado: bool
    tipo_sinal: str  # "AC" ou "DC" — escolhido pelo operador no painel


def ler_telemetria(
    tipo_sinal: str = "AC",
    corrente_base: float = 5.0,
    disjuntor_fechado: bool = True,
) -> LeituraTelemetria:
    """Simula a leitura de tensão/corrente do quadro elétrico, para o tipo de sinal
    escolhido pelo operador ('AC' residencial ~220V ou 'DC' baixa tensão ~12V).

    Na Unidade 4 esta função é substituída pela leitura via porta serial,
    mantendo o mesmo retorno (LeituraTelemetria).
    """
    tensao_nominal = TENSAO_NOMINAL_DC if tipo_sinal == "DC" else TENSAO_NOMINAL_AC
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
        tipo_sinal=tipo_sinal,
    )


def calcular_potencia(leitura: LeituraTelemetria) -> float:
    """P = V × I. Retorna 0 quando o disjuntor está aberto."""
    if not leitura.disjuntor_fechado:
        return 0.0
    return leitura.tensao * leitura.corrente


def corrente_excedida(leitura: LeituraTelemetria, configuracao: ConfiguracaoSistema) -> bool:
    return leitura.corrente > configuracao.corrente_maxima


def classificar_circuito(leitura: LeituraTelemetria) -> str:
    """Classifica o efetuador (garra) usado para medir `leitura`, seguindo a árvore de
    triagem do documento técnico (docs/SkyVolt_Documento.tex, Seção 4.2 — Sistema de
    medição): AC >=100V no campo -> garra de campo (sem contato); AC <100V ou DC
    (sempre <=100V por restrição de projeto, RNF06) -> garra de contato.
    """
    if leitura.tipo_sinal == "DC":
        return "DC — Garra de Contato"
    if leitura.tensao >= 100:
        return "AC — Garra de Campo"
    return "AC — Garra de Contato"


def avaliar_qualidade(leitura: LeituraTelemetria, configuracao: ConfiguracaoSistema) -> str:
    """Classifica a leitura como 'Normal', 'Fora da faixa' ou 'Circuito aberto'.

    Com o disjuntor aberto a corrente é sempre 0 (dentro de qualquer faixa configurada),
    então essa checagem vem antes para não classificar erroneamente como 'Normal'.
    """
    if not leitura.disjuntor_fechado:
        return "Circuito aberto"
    if configuracao.esta_dentro_da_faixa(leitura.tensao, leitura.corrente, leitura.tipo_sinal):
        return "Normal"
    return "Fora da faixa"
