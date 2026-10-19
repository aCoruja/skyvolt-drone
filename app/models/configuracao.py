from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from typing import ClassVar

from app.database.connection import DATA_DIR
from app.models.logger_service import log_info, log_warning

CONFIG_JSON_PATH = os.path.join(DATA_DIR, "config.json")
CONFIG_JSON_NOME = "data/config.json"  # caminho curto usado nas mensagens de log


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


@dataclass
class ParametrosSerial:
    """Parâmetros do painel de comunicação serial (configuração local do drone)."""

    porta_com: str = "COM1"
    baud_rate: str = "9600"
    timeout_s: int = 5


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

    campos_nao_negativos = {
        "Tensão mínima AC": configuracao.tensao_minima_ac,
        "Tensão máxima AC": configuracao.tensao_maxima_ac,
        "Tensão mínima DC": configuracao.tensao_minima_dc,
        "Tensão máxima DC": configuracao.tensao_maxima_dc,
    }
    for nome, valor in campos_nao_negativos.items():
        if valor < 0:
            erros.append(f"{nome} não pode ser negativa ({valor}).")

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


def carregar_parametros_json() -> tuple[ConfiguracaoSistema, ParametrosSerial]:
    """Lê data/config.json. Se o arquivo não existir (os.path.exists), cria-o com os
    valores default. Se estiver corrompido ou com valores inválidos, registra WARNING
    e usa os defaults (o arquivo é regravado no próximo salvamento)."""
    if not os.path.exists(CONFIG_JSON_PATH):
        log_warning(f"Arquivo {CONFIG_JSON_NOME} inexistente. Criando com valores default.")
        config, serial = ConfiguracaoSistema(), ParametrosSerial()
        salvar_parametros_json(config, serial)
        return config, serial

    try:
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)

        limites = dados.get("limites_seguranca", {})
        padrao = ConfiguracaoSistema()
        config = ConfiguracaoSistema(
            tensao_minima_ac=float(limites.get("tensao_minima_ac", padrao.tensao_minima_ac)),
            tensao_maxima_ac=float(limites.get("tensao_maxima_ac", padrao.tensao_maxima_ac)),
            tensao_minima_dc=float(limites.get("tensao_minima_dc", padrao.tensao_minima_dc)),
            tensao_maxima_dc=float(limites.get("tensao_maxima_dc", padrao.tensao_maxima_dc)),
            corrente_maxima=float(limites.get("corrente_maxima", padrao.corrente_maxima)),
            disjuntor_automatico=bool(limites.get("disjuntor_automatico", padrao.disjuntor_automatico)),
            tempo_reacao_s=int(limites.get("tempo_reacao_s", padrao.tempo_reacao_s)),
            intervalo_leitura_s=int(limites.get("intervalo_leitura_s", padrao.intervalo_leitura_s)),
            periodo_historico=str(limites.get("periodo_historico", padrao.periodo_historico)),
        )

        comunicacao = dados.get("comunicacao_serial", {})
        serial = ParametrosSerial(
            porta_com=str(comunicacao.get("porta_com", ParametrosSerial.porta_com)),
            baud_rate=str(comunicacao.get("baud_rate", ParametrosSerial.baud_rate)),
            timeout_s=int(comunicacao.get("timeout_s", ParametrosSerial.timeout_s)),
        )
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError) as erro:
        log_warning(f"Falha ao ler {CONFIG_JSON_NOME}: {erro}. Usando parâmetros default.")
        return ConfiguracaoSistema(), ParametrosSerial()

    erros = validar_configuracao(config)
    if erros:
        log_warning(f"Limites inválidos em config.json ({'; '.join(erros)}). Usando limites default.")
        config = ConfiguracaoSistema()

    log_info(f"Parâmetros carregados de {CONFIG_JSON_NOME}.")
    return config, serial


def salvar_parametros_json(config: ConfiguracaoSistema, serial: ParametrosSerial) -> None:
    """Persiste os parâmetros de comunicação serial e os limites iniciais em JSON.
    Lança OSError se não for possível gravar o arquivo."""
    os.makedirs(os.path.dirname(CONFIG_JSON_PATH), exist_ok=True)
    dados = {
        "comunicacao_serial": asdict(serial),
        "limites_seguranca": {
            "tensao_minima_ac": config.tensao_minima_ac,
            "tensao_maxima_ac": config.tensao_maxima_ac,
            "tensao_minima_dc": config.tensao_minima_dc,
            "tensao_maxima_dc": config.tensao_maxima_dc,
            "corrente_maxima": config.corrente_maxima,
            "disjuntor_automatico": config.disjuntor_automatico,
            "tempo_reacao_s": config.tempo_reacao_s,
            "intervalo_leitura_s": config.intervalo_leitura_s,
            "periodo_historico": config.periodo_historico,
        },
    }
    with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    log_info(f"Arquivo {CONFIG_JSON_NOME} salvo.")
