# Destino no GitHub (repo skyvolt-drone): app/models/configuracao.py
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import ClassVar


@dataclass
class ConfiguracaoSistema:
    """Parâmetros de operação e alarme do painel, editados via ConfigDialog (app/ui/config_dialog.ui).

    Cada leitura de telemetria (app/models/telemetria.py) é comparada contra os limites de
    tensão (AC ou DC, conforme o modo de medição escolhido pelo operador) e de corrente aqui
    definidos para decidir se está 'Normal' ou 'Fora da faixa'. Quando fora da faixa com o
    disjuntor fechado, o corte automático (ver `disjuntor_automatico`/`tempo_reacao_s`) entra
    em ação se o operador não agir manualmente a tempo.
    """

    PERIODOS_DISPONIVEIS: ClassVar[list[str]] = ["6h", "12h", "24h", "7 dias"]

    # --- Limites de alarme (setpoints) — separados por tipo de sinal, já que a faixa
    # segura de um circuito AC residencial e de uma fonte/bateria DC é bem diferente
    # (ver docs/SkyVolt_Documento.tex, RNF06: DC sempre <=100V; AC até 220V) ---
    tensao_minima_ac: float = 198.0  # V — abaixo disso, leitura AC vira "Fora da faixa"
    tensao_maxima_ac: float = 242.0  # V — acima disso, idem
    tensao_minima_dc: float = 5.0  # V — abaixo disso, leitura DC vira "Fora da faixa"
    tensao_maxima_dc: float = 100.0  # V — acima disso, idem (limite de projeto RNF06)
    corrente_maxima: float = 15.0  # A — acima disso, entra em risco de corte automático

    # --- Corte automático do disjuntor ---
    disjuntor_automatico: bool = True  # se False, o corte por risco nunca é automático
    tempo_reacao_s: int = 5  # segundos de janela pro operador agir antes do corte automático

    # --- Amostragem e histórico ---
    intervalo_leitura_s: int = 2  # segundos entre leituras (Unidade 4: leitura serial real)
    periodo_historico: str = "24h"  # janela do gráfico de tendência — ver PERIODOS_DISPONIVEIS
    data_inicio: date = field(default_factory=date.today)  # data inicial do histórico consultado

    def esta_dentro_da_faixa(self, tensao: float, corrente: float, tipo_sinal: str) -> bool:
        """True se `tensao` está dentro da faixa mín/máx do `tipo_sinal` ('AC' ou 'DC')
        e `corrente` não excede corrente_maxima."""
        if tipo_sinal == "DC":
            tensao_ok = self.tensao_minima_dc <= tensao <= self.tensao_maxima_dc
        else:
            tensao_ok = self.tensao_minima_ac <= tensao <= self.tensao_maxima_ac
        return tensao_ok and corrente <= self.corrente_maxima


def configuracao_padrao() -> ConfiguracaoSistema:
    """Retorna a ConfiguracaoSistema com os valores padrão do sistema — usada ao abrir o
    app, antes do usuário editar qualquer coisa via ConfigDialog."""
    return ConfiguracaoSistema()


def copiar_configuracao(configuracao: ConfiguracaoSistema) -> ConfiguracaoSistema:
    """Retorna uma cópia independente de `configuracao`. Usada pelo ConfigDialog para editar
    os valores livremente na tela sem afetar a configuração ativa até o usuário confirmar."""
    return replace(configuracao)


def validar_configuracao(configuracao: ConfiguracaoSistema) -> list[str]:
    """Valida os campos de `configuracao` e retorna a lista de mensagens de erro encontradas
    (lista vazia significa configuração válida, pronta para ser aplicada)."""
    erros: list[str] = []

    if configuracao.tensao_minima_ac >= configuracao.tensao_maxima_ac:
        erros.append("A tensão mínima AC deve ser menor que a tensão máxima AC.")
    if configuracao.tensao_minima_dc >= configuracao.tensao_maxima_dc:
        erros.append("A tensão mínima DC deve ser menor que a tensão máxima DC.")
    if configuracao.corrente_maxima <= 0:
        erros.append("A corrente máxima deve ser positiva.")
    if configuracao.tempo_reacao_s <= 0:
        erros.append("O tempo de reação para corte automático deve ser positivo.")
    if configuracao.intervalo_leitura_s <= 0:
        erros.append("O intervalo de leitura deve ser positivo.")
    if configuracao.periodo_historico not in ConfiguracaoSistema.PERIODOS_DISPONIVEIS:
        erros.append(f"Período inválido: {configuracao.periodo_historico}.")

    return erros
