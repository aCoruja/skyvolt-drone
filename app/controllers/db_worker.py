from __future__ import annotations

import sqlite3

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from app.models.corte_emergencial import CorteEmergencialService
from app.models.repositorios import (
    TAG_DISJUNTOR,
    DispositivoRepository,
    EventoRepository,
    LeituraRepository,
    RegrasLimitesRepository,
)
from app.models.telemetria import calcular_potencia

EVENTOS_INICIAIS = 500


class DbWorker(QObject):
    """Todo acesso ao SQLite do MainController, numa QThread própria.
    Recebe pedidos por sinais enfileirados e responde só por sinais."""

    estado_inicial = pyqtSignal(object, str, object)  # limites (ou None), status do disjuntor, eventos
    evento_gravado = pyqtSignal(object)
    comando_concluido = pyqtSignal(object, object)    # ResultadoComando, contexto do pedido
    historico_pronto = pyqtSignal(int, object)        # id da consulta, [(t, v, i, p), ...]
    erro_banco = pyqtSignal(str, str)                 # operação, mensagem

    @pyqtSlot()
    def carregar_estado_inicial(self) -> None:
        try:
            limites = RegrasLimitesRepository.carregar()
            status = DispositivoRepository.obter_status(TAG_DISJUNTOR)
            eventos = EventoRepository.listar_todos(EVENTOS_INICIAIS)
        except sqlite3.Error as erro:
            self.erro_banco.emit("estado_inicial", str(erro))
            return
        self.estado_inicial.emit(limites, status, eventos)

    @pyqtSlot(object)
    def gravar_leitura(self, leitura) -> None:
        try:
            LeituraRepository.inserir(leitura, calcular_potencia(leitura))
        except sqlite3.Error as erro:
            self.erro_banco.emit("leitura", str(erro))

    @pyqtSlot(object)
    def gravar_evento(self, evento) -> None:
        try:
            EventoRepository.inserir(evento)
        except sqlite3.Error as erro:
            self.erro_banco.emit("evento", str(erro))
            return
        self.evento_gravado.emit(evento)

    @pyqtSlot(object)
    def executar_comando_disjuntor(self, ctx) -> None:
        try:
            resultado = CorteEmergencialService.executar(
                novo_status=ctx["novo_status"],
                descricao=ctx["descricao"],
                severidade=ctx["severidade"],
                simular_falha=ctx["simular_falha"],
            )
        except sqlite3.Error as erro:
            self.erro_banco.emit("disjuntor", str(erro))
            return
        self.comando_concluido.emit(resultado, ctx)

    @pyqtSlot(object)
    def salvar_limites(self, config) -> None:
        try:
            RegrasLimitesRepository.salvar(config)
        except sqlite3.Error as erro:
            self.erro_banco.emit("limites", str(erro))

    @pyqtSlot(int, object)
    def consultar_historico(self, id_consulta: int, filtro) -> None:
        try:
            if filtro["modo"] == "intervalo":
                pontos = LeituraRepository.consultar_intervalo(filtro["inicio"], filtro["fim"])
            else:
                pontos = LeituraRepository.consultar_ultimas(filtro["n"])
        except sqlite3.Error as erro:
            self.erro_banco.emit("historico", str(erro))
            return
        self.historico_pronto.emit(id_consulta, pontos)
