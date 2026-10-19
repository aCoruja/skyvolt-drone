from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem

from app.controllers.config_controller import abrir_configuracoes
from app.models.configuracao import carregar_parametros_json, salvar_parametros_json
from app.models.corte_emergencial import CorteEmergencialService
from app.models.dados_simulados import gerar_curva_consumo
from app.models.evento import COLUNAS, Evento, criar_evento, evento_para_linha
from app.models.formatacao import (
    estilo_qualidade,
    estilo_status_conexao,
    estilo_status_disjuntor,
    formatar_corrente,
    formatar_potencia,
    formatar_tensao,
    texto_status_conexao,
    texto_status_disjuntor,
)
from app.models.log_console import log_evento, log_sucesso
from app.models.logger_service import log_error, log_info, log_warning
from app.models.repositorios import (
    TAG_DISJUNTOR,
    DispositivoRepository,
    EventoRepository,
    RegrasLimitesRepository,
)
from app.models.telemetria import (
    TIPOS_SINAL_DISPONIVEIS,
    LeituraTelemetria,
    avaliar_qualidade,
    calcular_potencia,
    classificar_circuito,
    corrente_excedida,
    ler_telemetria,
)
from app.ui.main_window_ui import Ui_MainWindow

MAX_PONTOS_GRAFICO = 100
PORTAS_COM_DISPONIVEIS = ["COM1", "COM2", "COM3"]
BAUD_RATES_DISPONIVEIS = ["9600", "115200"]


class MainController(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.montar_janela()

    def showEvent(self, event: QShowEvent) -> None:
        """A tabela de eventos é sempre recarregada do SQLite ao exibir a janela."""
        super().showEvent(event)
        self.carregar_eventos_do_banco()

    def montar_janela(self) -> None:
        self.setupUi(self)
        self.criar_estado()
        self.carregar_grafico()
        self.preparar_tabela()
        self.preparar_modo_medicao()
        self.preparar_conectividade()

        self.btnAlternarDisjuntor.clicked.connect(self.alternar_disjuntor)
        self.btnConfiguracoes.clicked.connect(self.aplicar_configuracao)
        self.cmbTipoSinal.currentTextChanged.connect(self.atualizar_telemetria)
        self._timer_risco.timeout.connect(self._acionar_disjuntor_automatico)
        self.btnConectar.clicked.connect(self.conectar_lora)
        self.btnDesconectar.clicked.connect(self.desconectar_lora)
        self.btnConectarWifi.clicked.connect(self.conectar_wifi)
        self.btnDesconectarWifi.clicked.connect(self.desconectar_wifi)
        self.btnAplicarConfigDrone.clicked.connect(self.aplicar_config_drone)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.atualizar_telemetria)
        self._timer.start(self._config.intervalo_leitura_s * 1000)

        self.atualizar_telemetria()
        self.atualizar_disjuntor()
        log_sucesso("Janela principal montada — telemetria e gráfico em execução.")

    def criar_estado(self) -> None:
        # Parâmetros de comunicação serial e limites iniciais vêm do config.json;
        # os limites editados no diálogo ficam no SQLite e têm prioridade.
        self._config, self._serial = carregar_parametros_json()
        limites_banco = RegrasLimitesRepository.carregar()
        if limites_banco is not None:
            self._config = limites_banco
        else:
            RegrasLimitesRepository.salvar(self._config)
            log_info("Limites iniciais do config.json gravados na tabela regras_limites.")

        # Estado real do disjuntor persistido no banco
        self._disjuntor_fechado = DispositivoRepository.obter_status(TAG_DISJUNTOR) == "FECHADO"

        self._corrente_violada = False
        self._risco_ativo = False
        self._timer_risco = QTimer(self)
        self._timer_risco.setSingleShot(True)

        # Histórico simulado (24 pontos) posicionado terminando "agora", espaçado pelo
        # intervalo de leitura configurado, para a linha do tempo já nascer contínua.
        _horas, tensoes_simuladas, _correntes = gerar_curva_consumo()
        agora = datetime.now()
        intervalo = timedelta(seconds=self._config.intervalo_leitura_s)
        n = len(tensoes_simuladas)
        self._historico_tempos = [
            (agora - (n - i) * intervalo).timestamp() for i in range(n)
        ]
        self._historico_tensoes = tensoes_simuladas

    def carregar_grafico(self) -> None:
        pg.setConfigOptions(antialias=True)
        self.graficoConsumo.setAxisItems({"bottom": pg.DateAxisItem(orientation="bottom")})
        self.graficoConsumo.setBackground("w")
        self.graficoConsumo.setLabel("left", "Tensão (V)")
        self.graficoConsumo.setLabel("bottom", "Horário")
        self.graficoConsumo.showGrid(x=True, y=True, alpha=0.2)

        caneta = pg.mkPen(color="#4a67a3", width=3)
        preenchimento = pg.mkBrush(74, 103, 163, 60)
        self._curva_tensao = self.graficoConsumo.plot(
            self._historico_tempos,
            self._historico_tensoes,
            pen=caneta,
            symbol="o",
            symbolSize=6,
            symbolBrush="#4a67a3",
            symbolPen=None,
            fillLevel=min(self._historico_tensoes) * 0.98,
            brush=preenchimento,
        )

    def preparar_tabela(self) -> None:
        self.tblEventos.setColumnCount(len(COLUNAS))
        self.tblEventos.setHorizontalHeaderLabels(COLUNAS)
        self.tblEventos.horizontalHeader().setStretchLastSection(True)

    def carregar_eventos_do_banco(self) -> None:
        """Preenche a QTableWidget com o histórico do SQLite (Repository.listar_todos)."""
        try:
            eventos = EventoRepository.listar_todos()
        except sqlite3.Error as erro:
            log_error(f"Falha ao carregar o histórico de eventos do SQLite: {erro}.")
            QMessageBox.critical(self, "Erro de banco", f"Não foi possível carregar o histórico:\n{erro}")
            return
        self.tblEventos.setRowCount(0)
        for evento in reversed(eventos):  # mais antigo em cima, mais recente embaixo
            self.adicionar_evento(evento)
        self.tblEventos.resizeColumnsToContents()

    def preparar_modo_medicao(self) -> None:
        """O tipo de sinal (AC/DC) é escolhido pelo operador — não é auto-detectado
        nesta simulação — e decide qual garra (efetuador) o painel indica."""
        self.cmbTipoSinal.addItems(TIPOS_SINAL_DISPONIVEIS)

    def preparar_conectividade(self) -> None:
        """Três canais distintos, conforme a arquitetura de comunicação do documento
        técnico (docs/SkyVolt_Documento.tex, Seção 4.3): LoRa apenas recebe a
        telemetria de tensão/corrente/potência; WiFi carrega vídeo/comandos de voo
        (FPV); a porta COM — com seu baud rate e timeout — serve apenas para
        configuração local do drone, não para operação contínua. Porta, baud rate e
        timeout são lidos de/gravados em config.json."""
        self.atualizar_status_lora(conectado=False)
        self.atualizar_status_wifi(conectado=False)

        self.cmbPortaCOM.addItems(PORTAS_COM_DISPONIVEIS)
        if self._serial.porta_com not in PORTAS_COM_DISPONIVEIS:
            self.cmbPortaCOM.addItem(self._serial.porta_com)
        self.cmbPortaCOM.setCurrentText(self._serial.porta_com)

        self.cmbBaudRate.addItems(BAUD_RATES_DISPONIVEIS)
        if self._serial.baud_rate not in BAUD_RATES_DISPONIVEIS:
            self.cmbBaudRate.addItem(self._serial.baud_rate)
        self.cmbBaudRate.setCurrentText(self._serial.baud_rate)

        self.spnTimeout.setRange(1, 60)
        self.spnTimeout.setValue(self._serial.timeout_s)
        self.spnTimeout.setSuffix(" s")

    def atualizar_status_lora(self, conectado: bool) -> None:
        self.lblStatusConexao.setText(texto_status_conexao(conectado))
        self.lblStatusConexao.setStyleSheet(estilo_status_conexao(conectado))
        self.btnConectar.setEnabled(not conectado)
        self.btnDesconectar.setEnabled(conectado)

    def conectar_lora(self) -> None:
        self.atualizar_status_lora(conectado=True)
        log_sucesso("LoRa conectado (simulado) — recebendo tensão, corrente e potência.")

    def desconectar_lora(self) -> None:
        self.atualizar_status_lora(conectado=False)
        log_sucesso("LoRa desconectado — recepção de telemetria suspensa.")

    def atualizar_status_wifi(self, conectado: bool) -> None:
        self.lblStatusWifi.setText(texto_status_conexao(conectado))
        self.lblStatusWifi.setStyleSheet(estilo_status_conexao(conectado))
        self.btnConectarWifi.setEnabled(not conectado)
        self.btnDesconectarWifi.setEnabled(conectado)

    def conectar_wifi(self) -> None:
        self.atualizar_status_wifi(conectado=True)
        log_sucesso("WiFi conectado (simulado) — link de voo/FPV ativo.")

    def desconectar_wifi(self) -> None:
        self.atualizar_status_wifi(conectado=False)
        log_sucesso("WiFi desconectado — link de voo/FPV suspenso.")

    def aplicar_config_drone(self) -> None:
        """Configuração local do drone via porta COM (porta + baud rate + timeout) —
        ação pontual, não uma conexão contínua (essa é papel do LoRa)."""
        self._serial.porta_com = self.cmbPortaCOM.currentText()
        self._serial.baud_rate = self.cmbBaudRate.currentText()
        self._serial.timeout_s = self.spnTimeout.value()
        porta, baud, timeout = self._serial.porta_com, self._serial.baud_rate, self._serial.timeout_s

        try:
            salvar_parametros_json(self._config, self._serial)
        except OSError as erro:
            log_error(f"Falha ao salvar a configuração serial em config.json: {erro}.")
            QMessageBox.critical(self, "Configuração do drone", f"Não foi possível salvar config.json:\n{erro}")
            return

        log_info(f"Configuração serial salva: {porta} @ {baud} bps, timeout {timeout}s.")
        QMessageBox.information(
            self,
            "Configuração do drone",
            f"Parâmetros salvos em config.json e enviados ao drone pela porta {porta} "
            f"({baud} bps, timeout {timeout}s).",
        )

    def adicionar_evento(self, evento: Evento) -> None:
        linha = self.tblEventos.rowCount()
        self.tblEventos.insertRow(linha)
        for coluna, valor in enumerate(evento_para_linha(evento)):
            self.tblEventos.setItem(linha, coluna, QTableWidgetItem(valor))

    def registrar_evento(
        self, tipo: str, descricao: str, severidade: str, valor_medido: Optional[float] = None
    ) -> None:
        """Grava o evento no SQLite e, só depois de gravado, mostra na tabela."""
        evento = criar_evento(tipo, descricao, severidade, valor_medido)
        try:
            EventoRepository.inserir(evento)
        except sqlite3.Error as erro:
            log_error(f"Falha ao gravar evento '{tipo}: {descricao}' no histórico: {erro}.")
            return
        self.adicionar_evento(evento)
        self.tblEventos.scrollToBottom()
        log_evento(tipo, descricao, severidade)

    def atualizar_telemetria(self) -> None:
        leitura = ler_telemetria(
            tipo_sinal=self.cmbTipoSinal.currentText(), disjuntor_fechado=self._disjuntor_fechado
        )
        potencia = calcular_potencia(leitura)
        qualidade = avaliar_qualidade(leitura, self._config)

        self.lblTensaoValor.setText(formatar_tensao(leitura.tensao))
        self.lblCorrenteValor.setText(formatar_corrente(leitura.corrente))
        self.lblPotenciaValor.setText(formatar_potencia(potencia))
        self.lblQualidade.setText(qualidade)
        self.lblQualidade.setStyleSheet(estilo_qualidade(qualidade))
        self.lblModoMedicao.setText(classificar_circuito(leitura))

        self._historico_tempos.append(leitura.timestamp.timestamp())
        self._historico_tensoes.append(leitura.tensao)
        if len(self._historico_tempos) > MAX_PONTOS_GRAFICO:
            self._historico_tempos = self._historico_tempos[-MAX_PONTOS_GRAFICO:]
            self._historico_tensoes = self._historico_tensoes[-MAX_PONTOS_GRAFICO:]
        self._curva_tensao.setData(self._historico_tempos, self._historico_tensoes)

        self._auditar_corrente(leitura)
        self._avaliar_risco(leitura, qualidade)

    def _auditar_corrente(self, leitura: LeituraTelemetria) -> None:
        """Registra no smartgrid.log cada nova violação do limite de corrente (só na
        transição normal -> violado, para não repetir a cada leitura)."""
        violada = self._disjuntor_fechado and corrente_excedida(leitura, self._config)
        if violada and not self._corrente_violada:
            log_warning(
                f"Limite de corrente violado: {leitura.corrente:.2f}A "
                f"(Limite configurado: {self._config.corrente_maxima:.2f}A)."
            )
        self._corrente_violada = violada

    def _avaliar_risco(self, leitura: LeituraTelemetria, qualidade: str) -> None:
        """Inicia (ou cancela) a contagem regressiva de corte automático quando a leitura
        sai da faixa configurada com o disjuntor fechado — dá ao operador
        `tempo_reacao_s` segundos pra agir manualmente (botão Alternar Disjuntor)
        antes do corte automático, se habilitado em Configurações."""
        em_risco = self._disjuntor_fechado and qualidade == "Fora da faixa"

        if not em_risco:
            if self._risco_ativo:
                self._timer_risco.stop()
                self._risco_ativo = False
            return

        if self._risco_ativo or not self._config.disjuntor_automatico:
            return

        self._risco_ativo = True
        self._timer_risco.start(self._config.tempo_reacao_s * 1000)
        corrente_alta = corrente_excedida(leitura, self._config)
        motivo = "corrente alta" if corrente_alta else "tensão fora da faixa"
        self.registrar_evento(
            tipo="Risco",
            descricao=(
                f"Risco detectado ({motivo}) — corte automático em "
                f"{self._config.tempo_reacao_s}s se não houver ação manual"
            ),
            severidade="Alerta",
            valor_medido=leitura.corrente if corrente_alta else leitura.tensao,
        )

    def _acionar_disjuntor_automatico(self) -> None:
        self._risco_ativo = False
        if not self._disjuntor_fechado:
            return  # operador já agiu manualmente nesse meio tempo

        if not self._comandar_disjuntor(
            novo_status="ABERTO",
            descricao=f"Corte automático — operador não reagiu em {self._config.tempo_reacao_s}s",
            severidade="Critico",
        ):
            return
        QMessageBox.warning(
            self,
            "Corte automático",
            f"Risco não resolvido em {self._config.tempo_reacao_s}s — disjuntor aberto automaticamente.",
        )

    def atualizar_disjuntor(self) -> None:
        self.lblStatusDisjuntor.setText(texto_status_disjuntor(self._disjuntor_fechado))
        self.lblStatusDisjuntor.setStyleSheet(estilo_status_disjuntor(self._disjuntor_fechado))
        self.btnAlternarDisjuntor.setText(
            "⏻  Corte Emergencial" if self._disjuntor_fechado else "⏻  Religar Disjuntor"
        )

    def alternar_disjuntor(self) -> None:
        simular_falha = False
        if self._disjuntor_fechado:
            caixa = QMessageBox(self)
            caixa.setIcon(QMessageBox.Warning)
            caixa.setWindowTitle("Confirmar corte de emergência")
            caixa.setText("Abrir o disjuntor e cortar o fornecimento de energia?")
            btn_cortar = caixa.addButton("Corte Emergencial", QMessageBox.AcceptRole)
            btn_falha = caixa.addButton("Simular falha (teste de rollback)", QMessageBox.ActionRole)
            caixa.addButton("Cancelar", QMessageBox.RejectRole)
            caixa.exec_()
            if caixa.clickedButton() not in (btn_cortar, btn_falha):
                return
            simular_falha = caixa.clickedButton() is btn_falha
            novo_status, descricao, severidade = "ABERTO", "Corte emergencial manual do disjuntor", "Critico"
        else:
            resposta = QMessageBox.question(
                self,
                "Religar disjuntor",
                "Restabelecer o fornecimento e fechar o disjuntor?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                return
            novo_status, descricao, severidade = "FECHADO", "Comando de fechamento do disjuntor", "Info"

        if self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False

        self._comandar_disjuntor(novo_status, descricao, severidade, simular_falha)
        self.atualizar_telemetria()

    def _comandar_disjuntor(
        self, novo_status: str, descricao: str, severidade: str, simular_falha: bool = False
    ) -> bool:
        """Executa o comando como transação atômica (disjuntor + histórico) e sincroniza
        a tela com o que ficou gravado no banco — inclusive depois de um ROLLBACK."""
        resultado = CorteEmergencialService.executar(
            novo_status, descricao, severidade, simular_falha=simular_falha
        )
        self._disjuntor_fechado = resultado.status_no_banco == "FECHADO"
        self.atualizar_disjuntor()

        if not resultado.sucesso:
            log_error(f"Falha na operação de corte emergencial. Rollback executado: {resultado.erro}.")
            QMessageBox.critical(
                self,
                "Transação revertida (ROLLBACK)",
                f"O comando falhou e foi desfeito por completo:\n{resultado.erro}\n\n"
                f"Disjuntor no banco: {resultado.status_no_banco}. Nenhum evento foi gravado.",
            )
            return False

        self.adicionar_evento(resultado.evento)
        self.tblEventos.scrollToBottom()
        log_evento("Disjuntor", descricao, severidade)
        if novo_status == "ABERTO":
            log_warning(f"Corte de carga executado: {descricao}. Disjuntor ABERTO (COMMIT).")
        else:
            log_info(f"{descricao}. Disjuntor FECHADO (COMMIT).")
        return True

    def aplicar_configuracao(self) -> None:
        nova_configuracao = abrir_configuracoes(self, self._config)
        if nova_configuracao is None:
            return
        self._config = nova_configuracao
        try:
            salvar_parametros_json(self._config, self._serial)
        except OSError as erro:
            log_error(f"Limites salvos no SQLite, mas config.json não pôde ser atualizado: {erro}.")
        self._timer.setInterval(self._config.intervalo_leitura_s * 1000)
        if not self._config.disjuntor_automatico and self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False
        log_sucesso("Configuração aplicada — novos limites e intervalo de leitura em vigor.")
        QMessageBox.information(
            self, "Configuração aplicada", "Os novos limites foram salvos no banco e aplicados."
        )


def criar_janela_principal() -> MainController:
    """Ponto de entrada usado por app/main.py."""
    return MainController()
