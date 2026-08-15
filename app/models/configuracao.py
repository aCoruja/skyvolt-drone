# Destino no GitHub (repo skyvolt-drone): app/models/configuracao.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ConfiguracaoSistema:
    """Parâmetros de operação e alarme do painel, editados via ConfigDialog."""

    PERIODOS_DISPONIVEIS = ["6h", "12h", "24h", "7 dias"]

    tensao_minima: float = 198.0
    tensao_maxima: float = 242.0
    corrente_maxima: float = 15.0
    intervalo_leitura_s: int = 2
    periodo_historico: str = "24h"
    data_inicio: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if self.tensao_minima >= self.tensao_maxima:
            raise ValueError("tensao_minima deve ser menor que tensao_maxima")
        if self.corrente_maxima <= 0:
            raise ValueError("corrente_maxima deve ser positiva")
        if self.intervalo_leitura_s <= 0:
            raise ValueError("intervalo_leitura_s deve ser positivo")
        if self.periodo_historico not in self.PERIODOS_DISPONIVEIS:
            raise ValueError(f"periodo_historico inválido: {self.periodo_historico}")

    def esta_dentro_da_faixa(self, tensao: float, corrente: float) -> bool:
        return self.tensao_minima <= tensao <= self.tensao_maxima and corrente <= self.corrente_maxima
