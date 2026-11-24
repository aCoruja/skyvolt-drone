from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, Union

from app.models.configuracao import BAUD_RATES
from app.models.telemetria import TIPOS_SINAL_DISPONIVEIS, LeituraTelemetria

BAUD_INICIAL = BAUD_RATES[0]  # 9600 bps: toda conexão começa na velocidade mais lenta
ENCODING = "utf-8"


def montar_handshake(baud_alvo: int, intervalo_ms: int) -> bytes:
    """Primeiro pacote desktop -> placa (sempre a 9600 bps)."""
    pacote = {"cmd": "HANDSHAKE", "baud": baud_alvo, "intervalo_ms": intervalo_ms}
    return (json.dumps(pacote) + "\n").encode(ENCODING)


def montar_sync() -> bytes:
    """Confirmação já na nova velocidade (só usada se baud_alvo != 9600)."""
    return (json.dumps({"cmd": "SYNC"}) + "\n").encode(ENCODING)


def montar_comando_rele(disjuntor_fechado: bool) -> bytes:
    """Disjuntor do app -> chave K2 da sonda (Wi-Fi)."""
    estado = "FECHADO" if disjuntor_fechado else "ABERTO"
    return (json.dumps({"cmd": "RELE", "estado": estado}) + "\n").encode(ENCODING)


def montar_comando_modo(tipo_sinal: str) -> bytes:
    """Tipo de sinal escolhido no painel -> canal de tensão lido pela sonda (Wi-Fi)."""
    return (json.dumps({"cmd": "MODO", "tipo": tipo_sinal}) + "\n").encode(ENCODING)


def montar_ping() -> bytes:
    """Keepalive: sem comandos por alguns segundos, a sonda abre a chave K2 por segurança."""
    return (json.dumps({"cmd": "PING"}) + "\n").encode(ENCODING)


def extrair_ack(linha: Union[bytes, str]) -> Optional[dict]:
    dados = _decodificar_json(linha)
    return dados if dados is not None and "ack" in dados else None


def _decodificar_json(linha: Union[bytes, str]) -> Optional[dict]:
    texto = linha.decode(ENCODING, errors="replace") if isinstance(linha, bytes) else linha
    try:
        dados = json.loads(texto)
    except ValueError:
        return None  # linha truncada/inválida: descartar e esperar a próxima
    return dados if isinstance(dados, dict) else None


def e_ack(linha: Union[bytes, str], esperado: str) -> bool:
    dados = _decodificar_json(linha)
    return dados is not None and dados.get("ack") == esperado


def decodificar_telemetria(linha: Union[bytes, str], tipo_padrao: str = "AC") -> Optional[LeituraTelemetria]:
    """Converte {"t":..,"estado":"OK","tipo":"AC","v":..,"i":..} em LeituraTelemetria.
    Retorna None para ACK, estado != OK, valores nulos ou JSON inválido."""
    dados = _decodificar_json(linha)
    if dados is None or "ack" in dados or dados.get("estado") != "OK":
        return None
    try:
        tensao = float(dados["v"])
        corrente = float(dados["i"])
    except (KeyError, TypeError, ValueError):
        return None
    tipo = dados.get("tipo")
    if tipo not in TIPOS_SINAL_DISPONIVEIS:
        tipo = tipo_padrao
    return LeituraTelemetria(
        timestamp=datetime.now(),
        tensao=tensao,
        corrente=corrente,
        disjuntor_fechado=True,  # o controller ajusta com o estado real do disjuntor
        tipo_sinal=tipo,
    )


def listar_portas() -> list[str]:
    try:
        from serial.tools import list_ports

        return [p.device for p in list_ports.comports()]
    except Exception:  # noqa: BLE001 — enumeração é só conveniência
        return []
