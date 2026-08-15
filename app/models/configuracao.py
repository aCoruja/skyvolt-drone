# Destino no GitHub (repo skyvolt-drone): app/models/configuracao.py
from __future__ import annotations

from dataclasses import dataclass, field, replace
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

    def esta_dentro_da_faixa(self, tensao: float, corrente: float) -> bool:
        return self.tensao_minima <= tensao <= self.tensao_maxima and corrente <= self.corrente_maxima


def configuracao_padrao() -> ConfiguracaoSistema:
    """Retorna a ConfiguracaoSistema com os valores padrão do sistema."""
    return ConfiguracaoSistema()


def copiar_configuracao(configuracao: ConfiguracaoSistema) -> ConfiguracaoSistema:
    """Retorna uma cópia independente de `configuracao` (usada pelo dialog, que só
    deve alterar o original se o usuário confirmar)."""
    return replace(configuracao)


def validar_configuracao(configuracao: ConfiguracaoSistema) -> list[str]:
    """Valida os campos de `configuracao`. Retorna a lista de mensagens de erro
    (vazia se a configuração for válida)."""
    erros: list[str] = []
    if configuracao.tensao_minima >= configuracao.tensao_maxima:
        erros.append("A tensão mínima deve ser menor que a tensão máxima.")
    if configuracao.corrente_maxima <= 0:
        erros.append("A corrente máxima deve ser positiva.")
    if configuracao.intervalo_leitura_s <= 0:
        erros.append("O intervalo de leitura deve ser positivo.")
    if configuracao.periodo_historico not in ConfiguracaoSistema.PERIODOS_DISPONIVEIS:
        erros.append(f"Período inválido: {configuracao.periodo_historico}.")
    return erros
