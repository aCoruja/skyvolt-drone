# Destino no GitHub (repo skyvolt-drone): app/models/telemetria.py
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LeituraTelemetria:
    timestamp: datetime
    tensao: float
    corrente: float
    disjuntor_fechado: bool

    @property
    def potencia(self) -> float:
        return self.tensao * self.corrente if self.disjuntor_fechado else 0.0


class SensorTelemetria:
    """Simula a leitura de tensão/corrente do quadro elétrico.

    Na Unidade 4 esta classe é substituída pela leitura via porta serial,
    mantendo a mesma interface pública (proxima_leitura / alternar_disjuntor).
    """

    def __init__(self, tensao_nominal: float = 220.0, corrente_base: float = 5.0) -> None:
        self._tensao_nominal = tensao_nominal
        self._corrente_base = corrente_base
        self._disjuntor_fechado = True

    @property
    def disjuntor_fechado(self) -> bool:
        return self._disjuntor_fechado

    def alternar_disjuntor(self) -> bool:
        self._disjuntor_fechado = not self._disjuntor_fechado
        return self._disjuntor_fechado

    def proxima_leitura(self) -> LeituraTelemetria:
        variacao = random.uniform(-0.03, 0.03)
        tensao = round(self._tensao_nominal * (1 + variacao), 1)
        corrente = (
            round(max(0.0, random.gauss(self._corrente_base, 1.2)), 2)
            if self._disjuntor_fechado
            else 0.0
        )
        return LeituraTelemetria(
            timestamp=datetime.now(),
            tensao=tensao,
            corrente=corrente,
            disjuntor_fechado=self._disjuntor_fechado,
        )
