from __future__ import annotations

import threading
import time

import serial
from PyQt5.QtCore import QThread, pyqtSignal

from app.models.protocolo_serial import (
    BAUD_INICIAL,
    decodificar_telemetria,
    e_ack,
    montar_handshake,
    montar_sync,
)

LEITURA_TIMEOUT_S = 0.2  # readline curto: a thread enxerga o pedido de parada a cada 200 ms
TENTATIVAS_ACK = 3


class SerialWorker(QThread):
    """Conexão, handshake (sempre iniciando a 9600 bps) e recepção contínua.
    Nunca toca em widgets: só emite sinais."""

    estado_mudou = pyqtSignal(str)
    handshake_concluido = pyqtSignal(int)   # baud em operação
    leitura_recebida = pyqtSignal(object)   # LeituraTelemetria
    conexao_perdida = pyqtSignal(str)       # falha DEPOIS de conectar (cabo/porta caiu, silêncio)
    erro = pyqtSignal(str)                  # falha ao abrir porta / handshake sem ACK

    def __init__(
        self, porta: str, baud_alvo: int, intervalo_ms: int, timeout_s: int, tipo_padrao: str = "AC"
    ) -> None:
        super().__init__()
        self._porta = porta
        self._baud_alvo = baud_alvo
        self._intervalo_ms = intervalo_ms
        self._timeout_s = timeout_s
        self._tipo_padrao = tipo_padrao
        self._parar = threading.Event()

    # chamados pela GUI (thread-safe)
    def solicitar_parada(self) -> None:
        self._parar.set()

    def definir_tipo_padrao(self, tipo: str) -> None:
        self._tipo_padrao = tipo

    def run(self) -> None:
        try:
            ser = serial.Serial(self._porta, BAUD_INICIAL, timeout=LEITURA_TIMEOUT_S, write_timeout=1.0)
        except (serial.SerialException, OSError, ValueError) as erro:
            self.erro.emit(f"Não foi possível abrir {self._porta}: {erro}")
            return
        try:
            self.estado_mudou.emit(f"Handshake a {BAUD_INICIAL} bps…")
            if self._negociar(ser):
                self._receber(ser)
        except (serial.SerialException, OSError) as erro:
            if not self._parar.is_set():
                self.conexao_perdida.emit(str(erro))
        finally:
            try:
                ser.close()
            except (serial.SerialException, OSError):
                pass

    def _trocar(self, ser: serial.Serial, pacote: bytes, esperado: str) -> bool:
        for _ in range(TENTATIVAS_ACK):
            if self._parar.is_set():
                return False
            ser.reset_input_buffer()
            ser.write(pacote)
            ser.flush()
            limite = time.monotonic() + self._timeout_s
            while time.monotonic() < limite and not self._parar.is_set():
                linha = ser.readline()  # bloqueia no máx. 200 ms, e só nesta thread
                if linha and e_ack(linha, esperado):
                    return True
        return False

    def _negociar(self, ser: serial.Serial) -> bool:
        if not self._trocar(ser, montar_handshake(self._baud_alvo, self._intervalo_ms), "HANDSHAKE"):
            if not self._parar.is_set():
                self.erro.emit(f"Sem ACK do handshake a {BAUD_INICIAL} bps.")
            return False
        if self._baud_alvo != BAUD_INICIAL:
            self.estado_mudou.emit(f"Trocando para {self._baud_alvo} bps…")
            ser.baudrate = self._baud_alvo
            time.sleep(0.1)
            if not self._trocar(ser, montar_sync(), "SYNC"):
                if not self._parar.is_set():
                    self.erro.emit(f"Sem ACK de sincronismo a {self._baud_alvo} bps.")
                return False
        self.handshake_concluido.emit(self._baud_alvo)
        return True

    def _receber(self, ser: serial.Serial) -> None:
        silencio_max = max(float(self._timeout_s), 3 * self._intervalo_ms / 1000)
        ultimo = time.monotonic()
        while not self._parar.is_set():
            linha = ser.readline()
            if not linha:
                if time.monotonic() - ultimo > silencio_max:
                    self.conexao_perdida.emit(f"Sem telemetria há mais de {silencio_max:.0f}s.")
                    return
                continue
            ultimo = time.monotonic()
            leitura = decodificar_telemetria(linha, self._tipo_padrao)
            if leitura is not None:
                self.leitura_recebida.emit(leitura)
