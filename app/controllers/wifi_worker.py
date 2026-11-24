from __future__ import annotations

import queue
import socket
import threading
import time
from typing import Optional

from PyQt5.QtCore import QThread, pyqtSignal

from app.models.protocolo_serial import (
    BAUD_INICIAL,
    decodificar_telemetria,
    e_ack,
    extrair_ack,
    montar_handshake,
    montar_ping,
)

LEITURA_TIMEOUT_S = 0.2  # recv curto: a thread enxerga parada e fila de comandos a cada 200 ms
TENTATIVAS_ACK = 3
INTERVALO_PING_S = 2.0   # a sonda abre a chave K2 se ficar TIMEOUT_LINK_MS (6 s) sem comando
TAMANHO_MAX_LINHA = 4096


class WifiWorker(QThread):
    """Link TCP com a sonda (firmware/sonda-wifi): mesmo JSON por linha do serial,
    mais comandos RELE/MODO e PING de keepalive. Nunca toca em widgets: só emite sinais."""

    estado_mudou = pyqtSignal(str)
    handshake_concluido = pyqtSignal(str)   # "host:porta"
    leitura_recebida = pyqtSignal(object)   # LeituraTelemetria
    ack_recebido = pyqtSignal(object)       # dict com "ack" (exceto PING)
    conexao_perdida = pyqtSignal(str)       # falha DEPOIS de conectar
    erro = pyqtSignal(str)                  # falha ao conectar / handshake sem ACK

    def __init__(
        self, host: str, porta: int, intervalo_ms: int, timeout_s: int, tipo_padrao: str = "AC"
    ) -> None:
        super().__init__()
        self._host = host
        self._porta = porta
        self._intervalo_ms = intervalo_ms
        self._timeout_s = timeout_s
        self._tipo_padrao = tipo_padrao
        self._parar = threading.Event()
        self._fila: queue.Queue[bytes] = queue.Queue()
        self._buffer = b""

    # chamados pela GUI (thread-safe)
    def solicitar_parada(self) -> None:
        self._parar.set()

    def definir_tipo_padrao(self, tipo: str) -> None:
        self._tipo_padrao = tipo

    def enviar_comando(self, pacote: bytes) -> None:
        self._fila.put(pacote)

    def run(self) -> None:
        try:
            sock = socket.create_connection((self._host, self._porta), timeout=self._timeout_s)
        except OSError as erro:
            self.erro.emit(f"Não foi possível conectar em {self._host}:{self._porta}: {erro}")
            return
        try:
            sock.settimeout(LEITURA_TIMEOUT_S)
            self.estado_mudou.emit(f"Handshake com {self._host}…")
            if self._negociar(sock):
                self._receber(sock)
        except OSError as erro:
            if not self._parar.is_set():
                self.conexao_perdida.emit(str(erro) or erro.__class__.__name__)
        finally:
            sock.close()

    def _ler_linha(self, sock: socket.socket) -> Optional[bytes]:
        """Próxima linha completa, ou None se nada chegou em 200 ms."""
        while b"\n" not in self._buffer:
            try:
                bloco = sock.recv(1024)
            except socket.timeout:
                return None
            if not bloco:
                raise ConnectionError("a sonda fechou a conexão")
            self._buffer += bloco
            if len(self._buffer) > TAMANHO_MAX_LINHA and b"\n" not in self._buffer:
                self._buffer = b""  # lixo sem fim de linha
        linha, self._buffer = self._buffer.split(b"\n", 1)
        return linha

    def _negociar(self, sock: socket.socket) -> bool:
        # Baud não se aplica ao Wi-Fi: com BAUD_INICIAL a sonda não espera SYNC.
        pacote = montar_handshake(BAUD_INICIAL, self._intervalo_ms)
        for _ in range(TENTATIVAS_ACK):
            if self._parar.is_set():
                return False
            sock.sendall(pacote)
            limite = time.monotonic() + self._timeout_s
            while time.monotonic() < limite and not self._parar.is_set():
                linha = self._ler_linha(sock)
                if linha and e_ack(linha, "HANDSHAKE"):
                    self.handshake_concluido.emit(f"{self._host}:{self._porta}")
                    return True
        if not self._parar.is_set():
            self.erro.emit(f"Sem ACK do handshake de {self._host}:{self._porta}.")
        return False

    def _enviar_fila(self, sock: socket.socket) -> None:
        while True:
            try:
                pacote = self._fila.get_nowait()
            except queue.Empty:
                return
            sock.sendall(pacote)

    def _receber(self, sock: socket.socket) -> None:
        silencio_max = max(float(self._timeout_s), 3 * self._intervalo_ms / 1000)
        ultimo = time.monotonic()
        proximo_ping = ultimo
        while not self._parar.is_set():
            if time.monotonic() >= proximo_ping:
                sock.sendall(montar_ping())
                proximo_ping = time.monotonic() + INTERVALO_PING_S
            self._enviar_fila(sock)

            linha = self._ler_linha(sock)
            if linha is None:
                if time.monotonic() - ultimo > silencio_max:
                    self.conexao_perdida.emit(f"Sonda sem resposta há mais de {silencio_max:.0f}s.")
                    return
                continue
            ultimo = time.monotonic()

            ack = extrair_ack(linha)
            if ack is not None:
                if ack.get("ack") != "PING":
                    self.ack_recebido.emit(ack)
                continue
            leitura = decodificar_telemetria(linha, self._tipo_padrao)
            if leitura is not None:
                self.leitura_recebida.emit(leitura)
