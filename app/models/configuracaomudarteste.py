from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from typing import ClassVar

from app.database.connection import BASE_DIR
from app.models.logger_service import log_info, log_warning

CONFIG_JSON_PATH = os.path.join(BASE_DIR, "data", "config.json")


@dataclass
class ConfiguracaoSistema:
    PERIODOS_DISPONIVEIS: ClassVar[list[str]] = ["6h", "12h", "24h", "7 dias"]

    tensao_minima_ac: float = 198.0
    tensao_maxima_ac: float = 242.0
    tensao_minima_dc: float = 5.0
    tensao_maxima_dc: float = 100.0
    corrente_maxima: float = 15.0

    disjuntor_automatico: bool = True
    tempo_reacao_s: int = 5
    intervalo_leitura_s: int = 2
    periodo_historico: str = "24h"
    data_inicio: date = field(default_factory=date.today)

    def esta_dentro_da_faixa(self, tensao: float, corrente: float, tipo_sinal: str) -> bool:
        if tipo_sinal == "DC":
            tensao_ok = self.tensao_minima_dc <= tensao <= self.tensao_maxima_dc
        else:
            tensao_ok = self.tensao_minima_ac <= tensao <= self.tensao_maxima_ac
        return tensao_ok and corrente <= self.corrente_maxima


@dataclass
class ParametrosSerial:
    porta_com: str = "COM1"
    baud_rate: str = "9600"
    timeout_s: int = 5


def configuracao_padrao() -> ConfiguracaoSistema:
    return ConfiguracaoSistema()


def copiar_configuracao(configuracao: ConfiguracaoSistema) -> ConfiguracaoSistema:
    return replace(configuracao)


def validar_configuracao(configuracao: ConfiguracaoSistema) -> list[str]:
    """Validações preventivas exigidas no edital (bloqueia negativos e incoerências)."""
    erros: list[str] = []

    if configuracao.tensao_minima_ac < 0 or configuracao.tensao_maxima_ac < 0:
        erros.append("Os valores de tensão AC não podem ser negativos.")
    if configuracao.tensao_minima_ac >= configuracao.tensao_maxima_ac:
        erros.append("A tensão mínima AC deve ser estritamente menor que a tensão máxima AC.")

    if configuracao.tensao_minima_dc < 0 or configuracao.tensao_maxima_dc < 0:
        erros.append("Os valores de tensão DC não podem ser negativos.")
    if configuracao.tensao_minima_dc >= configuracao.tensao_maxima_dc:
        erros.append("A tensão mínima DC deve ser estritamente menor que a tensão máxima DC.")

    if configuracao.corrente_maxima <= 0:
        erros.append("A corrente máxima deve ser estritamente maior que zero.")
    if configuracao.tempo_reacao_s <= 0:
        erros.append("O tempo de reação deve ser maior que zero.")
    if configuracao.intervalo_leitura_s <= 0:
        erros.append("O intervalo de leitura deve ser maior que zero.")
    if configuracao.periodo_historico not in ConfiguracaoSistema.PERIODOS_DISPONIVEIS:
        erros.append(f"Período de histórico selecionado inválido: {configuracao.periodo_historico}.")

    return erros


def carregar_parametros_json() -> tuple[ConfiguracaoSistema, ParametrosSerial]:
    """Valida a existência de config.json via os.path.exists.
    Se não existir, cria-o automaticamente com parâmetros default."""
    os.makedirs(os.path.dirname(CONFIG_JSON_PATH), exist_ok=True)

    if not os.path.exists(CONFIG_JSON_PATH):
        log_warning(f"Arquivo '{CONFIG_JSON_PATH}' inexistente. Criando arquivo com defaults.")
        config_default = ConfiguracaoSistema()
        serial_default = ParametrosSerial()
        salvar_parametros_json(config_default, serial_default)
        return config_default, serial_default

    try:
        with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)

        cfg_dict = dados.get("limites_seguranca", {})
        config = ConfiguracaoSistema(
            tensao_minima_ac=float(cfg_dict.get("tensao_minima_ac", 198.0)),
            tensao_maxima_ac=float(cfg_dict.get("tensao_maxima_ac", 242.0)),
            tensao_minima_dc=float(cfg_dict.get("tensao_minima_dc", 5.0)),
            tensao_maxima_dc=float(cfg_dict.get("tensao_maxima_dc", 100.0)),
            corrente_maxima=float(cfg_dict.get("corrente_maxima", 15.0)),
            disjuntor_automatico=bool(cfg_dict.get("disjuntor_automatico", True)),
            tempo_reacao_s=int(cfg_dict.get("tempo_reacao_s", 5)),
            intervalo_leitura_s=int(cfg_dict.get("intervalo_leitura_s", 2)),
            periodo_historico=str(cfg_dict.get("periodo_historico", "24h")),
        )

        ser_dict = dados.get("comunicacao_serial", {})
        serial = ParametrosSerial(
            porta_com=str(ser_dict.get("porta_com", "COM1")),
            baud_rate=str(ser_dict.get("baud_rate", "9600")),
            timeout_s=int(ser_dict.get("timeout_s", 5)),
        )
        return config, serial
    except Exception as e:
        log_warning(f"Erro ao ler {CONFIG_JSON_PATH}: {e}. Retornando parâmetros default.")
        return ConfiguracaoSistema(), ParametrosSerial()


def salvar_parametros_json(config: ConfiguracaoSistema, serial: ParametrosSerial) -> None:
    """Persiste parâmetros no arquivo estruturado JSON."""
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
    log_info("Arquivo estruturado 'data/config.json' atualizado com sucesso.")
