from __future__ import annotations

from dataclasses import replace
from typing import Optional

import pyqtgraph as pg
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QInputDialog, QMainWindow, QMessageBox, QTableWidgetItem

from app.controllers.config_controller import abrir_configuracoes
from app.controllers.db_worker import DbWorker
from app.controllers.serial_worker import SerialWorker
from app.controllers.wifi_worker import WifiWorker
from app.models.configuracao import (
    BAUD_RATES,
    ParametrosWifi,
    carregar_parametros_json,
    carregar_parametros_wifi,
    salvar_parametros_json,
    salvar_parametros_wifi,
)
from app.models.evento import COLUNAS, Evento, criar_evento, evento_para_linha
from app.models.formatacao import (
    estilo_qualidade,
    estilo_status_conexao,
    estilo_status_disjuntor,
    formatar_corrente,
    formatar_potencia,
    formatar_tensao,
    texto_status_disjuntor,
)
from app.models.log_console import log_evento, log_sucesso
from app.models.logger_service import log_error, log_info, log_warning
from app.models.protocolo_serial import listar_portas, montar_comando_modo, montar_comando_rele
from app.models.telemetria import (
    TIPOS_SINAL_DISPONIVEIS,
    LeituraTelemetria,
    avaliar_qualidade,
    calcular_potencia,
    classificar_circuito,
    corrente_excedida,
)
from app.ui.main_window_ui import Ui_MainWindow
from app.ui.painel_historico import PainelHistorico

MAX_PONTOS_GRAFICO = 100
BAUD_RATES_DISPONIVEIS = [str(b) for b in BAUD_RATES]
INTERVALO_RECONEXAO_MS = 3000
TIMEOUT_ACK_RELE_MS = 3000


class MainController(QMainWindow, Ui_MainWindow):
    """Mediador View <-> Model. Não faz I/O bloqueante: serial e SQLite rodam em
    QThreads dedicadas (SerialWorker e DbWorker) e se comunicam só por sinais."""

    # Pedidos à thread de banco (conexões enfileiradas entre threads)
    pedir_estado_inicial = pyqtSignal()
    pedir_gravar_leitura = pyqtSignal(object)
    pedir_gravar_evento = pyqtSignal(object)
    pedir_comando_disjuntor = pyqtSignal(object)
    pedir_salvar_limites = pyqtSignal(object)
    pedir_historico = pyqtSignal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self.montar_janela()

    def montar_janela(self) -> None:
        self.setupUi(self)
        self.criar_estado()
        self.carregar_grafico()
        self.montar_painel_historico()
        self.preparar_tabela()
        self.preparar_modo_medicao()
        self.preparar_conectividade()
        self.iniciar_thread_banco()

        self.btnAlternarDisjuntor.clicked.connect(self.alternar_disjuntor)
        self.btnConfiguracoes.clicked.connect(self.aplicar_configuracao)
        self.cmbTipoSinal.currentTextChanged.connect(self._tipo_sinal_mudou)
        self._timer_risco.timeout.connect(self._acionar_disjuntor_automatico)
        self._timer_reconexao.timeout.connect(self._tentar_reconectar)
        self._timer_reconexao_wifi.timeout.connect(self._tentar_reconectar_wifi)
        self._timer_ack_rele.timeout.connect(self._rele_sem_ack)
        self.btnConectar.clicked.connect(self._clique_conectar)
        self.btnDesconectar.clicked.connect(self.desconectar_serial)
        self.btnConectarWifi.clicked.connect(self.conectar_wifi)
        self.btnDesconectarWifi.clicked.connect(self.desconectar_wifi)
        self.btnAplicarConfigDrone.clicked.connect(self.aplicar_config_drone)

        self.atualizar_disjuntor()
        log_sucesso("Janela principal montada — threads de banco e serial prontas.")

    def criar_estado(self) -> None:
        self._config, self._serial = carregar_parametros_json()
        self._disjuntor_fechado = True  # valor real chega da thread de banco (estado_inicial)
        self._corrente_violada = False
        self._risco_ativo = False
        self._timer_risco = QTimer(self)
        self._timer_risco.setSingleShot(True)
        self._timer_reconexao = QTimer(self)
        self._timer_reconexao.setSingleShot(True)
        self._timer_reconexao.setInterval(INTERVALO_RECONEXAO_MS)

        self._wifi = carregar_parametros_wifi()
        self._wifi_worker: Optional[WifiWorker] = None
        self._wifi_reconectar = False
        self._wifi_em_reconexao = False
        self._wifi_desconexao_manual = False
        self._timer_reconexao_wifi = QTimer(self)
        self._timer_reconexao_wifi.setSingleShot(True)
        self._timer_reconexao_wifi.setInterval(INTERVALO_RECONEXAO_MS)
        self._rele_esperado: Optional[str] = None
        self._timer_ack_rele = QTimer(self)
        self._timer_ack_rele.setSingleShot(True)
        self._timer_ack_rele.setInterval(TIMEOUT_ACK_RELE_MS)

        self._serial_worker: Optional[SerialWorker] = None
        self._reconectar = False
        self._em_reconexao = False
        self._desconexao_manual = False
        self._encerrando = False
        self._modo_historico = False
        self._id_consulta = 0
        self._ultima_leitura: Optional[LeituraTelemetria] = None
        self._historico_tempos: list[float] = []
        self._historico_tensoes: list[float] = []

    def carregar_grafico(self) -> None:
        pg.setConfigOptions(antialias=True)
        self.graficoConsumo.setAxisItems({"bottom": pg.DateAxisItem(orientation="bottom")})
        self.graficoConsumo.setBackground("w")
        self.graficoConsumo.setLabel("left", "Tensão (V)")
        self.graficoConsumo.setLabel("bottom", "Horário")
        self.graficoConsumo.showGrid(x=True, y=True, alpha=0.2)
        self._curva_tensao = self.graficoConsumo.plot(
            [], [], pen=pg.mkPen(color="#4a67a3", width=3),
            symbol="o", symbolSize=6, symbolBrush="#4a67a3", symbolPen=None,
        )

    # ------------------------------------------------------------------ banco (thread)
    def iniciar_thread_banco(self) -> None:
        self._thread_db = QThread()
        self._db = DbWorker()
        self._db.moveToThread(self._thread_db)
        self._thread_db.finished.connect(self._db.deleteLater)

        self.pedir_estado_inicial.connect(self._db.carregar_estado_inicial)
        self.pedir_gravar_leitura.connect(self._db.gravar_leitura)
        self.pedir_gravar_evento.connect(self._db.gravar_evento)
        self.pedir_comando_disjuntor.connect(self._db.executar_comando_disjuntor)
        self.pedir_salvar_limites.connect(self._db.salvar_limites)
        self.pedir_historico.connect(self._db.consultar_historico)

        self._db.estado_inicial.connect(self._aplicar_estado_inicial)
        self._db.evento_gravado.connect(self._evento_gravado)
        self._db.comando_concluido.connect(self._comando_concluido)
        self._db.historico_pronto.connect(self._historico_pronto)
        self._db.erro_banco.connect(self._erro_banco)

        self._thread_db.start()
        self.pedir_estado_inicial.emit()

    def _aplicar_estado_inicial(self, limites, status: str, eventos) -> None:
        if limites is not None:
            self._config = limites
        else:
            self.pedir_salvar_limites.emit(self._config)
            log_info("Limites iniciais do config.json enviados à thread de banco.")
        self._disjuntor_fechado = status == "FECHADO"
        self.atualizar_disjuntor()
        self.tblEventos.setRowCount(0)
        for evento in reversed(eventos):  # mais antigo em cima, mais recente embaixo
            self.adicionar_evento(evento)
        self.tblEventos.resizeColumnsToContents()

    def _evento_gravado(self, evento: Evento) -> None:
        self.adicionar_evento(evento)
        self.tblEventos.scrollToBottom()
        log_evento(evento.tipo_evento, evento.descricao, evento.severidade)

    def _erro_banco(self, operacao: str, mensagem: str) -> None:
        log_error(f"Falha de banco na operação '{operacao}': {mensagem}.")
        self.statusBar().showMessage(f"Erro de banco ({operacao}): {mensagem}", 8000)
        if operacao == "historico":
            self.painelHistorico.definir_ocupado(False)
            QMessageBox.critical(self, "Erro de banco", f"Falha na consulta ao histórico:\n{mensagem}")
        elif operacao == "disjuntor":
            self.btnAlternarDisjuntor.setEnabled(True)

    def registrar_evento(
        self, tipo: str, descricao: str, severidade: str, valor_medido: Optional[float] = None
    ) -> None:
        """Cria o evento (Model) e manda gravar na thread de banco; a tabela só
        ganha a linha quando o sinal evento_gravado volta."""
        self.pedir_gravar_evento.emit(criar_evento(tipo, descricao, severidade, valor_medido))

    # ------------------------------------------------------------------ serial (thread)
    def preparar_conectividade(self) -> None:
        """LoRa/serial e Wi-Fi (sonda, firmware/sonda-wifi) para telemetria, e configuração
        local (porta COM, baud alvo e timeout, lidos de/gravados em config.json)."""
        self._mostrar_link("Desconectado", ativo=False)
        self._mostrar_wifi("Desconectado", ativo=False)

        self.cmbPortaCOM.setEditable(True)  # aceita porta virtual digitada (com0com/socat)
        self.cmbPortaCOM.addItems(listar_portas())
        if self.cmbPortaCOM.findText(self._serial.porta_com) < 0:
            self.cmbPortaCOM.addItem(self._serial.porta_com)
        self.cmbPortaCOM.setCurrentText(self._serial.porta_com)

        self.cmbBaudRate.addItems(BAUD_RATES_DISPONIVEIS)
        self.cmbBaudRate.setCurrentText(self._serial.baud_rate)

        self.spnTimeout.setRange(1, 60)
        self.spnTimeout.setValue(self._serial.timeout_s)
        self.spnTimeout.setSuffix(" s")

    def _mostrar_link(self, texto: str, ativo: bool) -> None:
        self.lblStatusConexao.setText(texto)
        self.lblStatusConexao.setStyleSheet(estilo_status_conexao(ativo))
        vivo = self._serial_worker is not None
        self.btnConectar.setEnabled(not vivo)
        self.btnDesconectar.setEnabled(vivo)

    def _clique_conectar(self) -> None:
        self._em_reconexao = False
        self.conectar_serial()

    def conectar_serial(self) -> None:
        if self._serial_worker is not None:
            return
        porta = self.cmbPortaCOM.currentText().strip()
        worker = SerialWorker(
            porta=porta,
            baud_alvo=int(self.cmbBaudRate.currentText()),
            intervalo_ms=self._config.intervalo_leitura_s * 1000,
            timeout_s=self.spnTimeout.value(),
            tipo_padrao=self.cmbTipoSinal.currentText(),
        )
        worker.estado_mudou.connect(self._serial_estado)
        worker.handshake_concluido.connect(self._serial_handshake_ok)
        worker.leitura_recebida.connect(self.processar_leitura)
        worker.conexao_perdida.connect(self._serial_perdida)
        worker.erro.connect(self._serial_erro)
        worker.finished.connect(self._serial_finalizada)
        worker.finished.connect(worker.deleteLater)
        self._serial_worker = worker
        self._reconectar = True
        self._desconexao_manual = False
        self._mostrar_link(f"Conectando em {porta}…", False)
        worker.start()

    def desconectar_serial(self) -> None:
        self._reconectar = False
        self._em_reconexao = False
        self._desconexao_manual = True
        self._timer_reconexao.stop()
        if self._serial_worker is not None:
            self._serial_worker.solicitar_parada()  # encerramento cooperativo
            self._mostrar_link("Desconectando…", False)
        else:
            self._mostrar_link("Desconectado", False)

    def _serial_estado(self, texto: str) -> None:
        self._mostrar_link(texto, False)

    def _serial_handshake_ok(self, baud: int) -> None:
        self._em_reconexao = False
        self._mostrar_link(f"Conectado @ {baud} bps", True)
        log_sucesso(f"Handshake concluído (início a 9600 bps, operando a {baud} bps).")
        self.registrar_evento("Comunicação", f"Handshake concluído — operando a {baud} bps", "Info")

    def _serial_perdida(self, mensagem: str) -> None:
        log_error(f"Link serial perdido: {mensagem}")
        self._em_reconexao = True
        self._mostrar_link("Link perdido — reconectando…", False)
        self.registrar_evento("Comunicação", f"Link serial perdido: {mensagem}", "Critico")
        if self._reconectar:
            self._timer_reconexao.start()

    def _serial_erro(self, mensagem: str) -> None:
        log_error(mensagem)
        self.statusBar().showMessage(mensagem, 10000)
        if self._em_reconexao and self._reconectar:
            self._mostrar_link("Link perdido — reconectando…", False)
            self._timer_reconexao.start()  # a porta pode ainda não ter voltado
            return
        self._reconectar = False
        self._mostrar_link("Falha na conexão", False)
        self.registrar_evento("Comunicação", mensagem, "Alerta")

    def _serial_finalizada(self) -> None:
        self._serial_worker = None
        if self._encerrando:
            return
        texto = "Desconectado" if self._desconexao_manual else self.lblStatusConexao.text()
        self._desconexao_manual = False
        self._mostrar_link(texto, False)

    def _tentar_reconectar(self) -> None:
        if self._reconectar and self._serial_worker is None:
            self.conectar_serial()

    def _tipo_sinal_mudou(self, tipo: str) -> None:
        if self._serial_worker is not None:
            self._serial_worker.definir_tipo_padrao(tipo)
        if self._wifi_worker is not None:
            self._wifi_worker.definir_tipo_padrao(tipo)
            self._wifi_worker.enviar_comando(montar_comando_modo(tipo))  # canal AC/DC da sonda

    # ------------------------------------------------------------------ telemetria
    def processar_leitura(self, leitura: LeituraTelemetria) -> None:
        """Slot do sinal leitura_recebida (thread serial)."""
        leitura = replace(leitura, disjuntor_fechado=self._disjuntor_fechado)
        self._ultima_leitura = leitura
        self.pedir_gravar_leitura.emit(leitura)  # persistência na thread de banco

        self._historico_tempos.append(leitura.timestamp.timestamp())
        self._historico_tensoes.append(leitura.tensao)
        self._historico_tempos = self._historico_tempos[-MAX_PONTOS_GRAFICO:]
        self._historico_tensoes = self._historico_tensoes[-MAX_PONTOS_GRAFICO:]
        if not self._modo_historico:  # modo tempo real: cada amostra atualiza a curva
            self._curva_tensao.setData(self._historico_tempos, self._historico_tensoes)

        self._exibir_leitura(leitura)

    def _exibir_leitura(self, leitura: LeituraTelemetria) -> None:
        potencia = calcular_potencia(leitura)
        qualidade = avaliar_qualidade(leitura, self._config)
        self.lblTensaoValor.setText(formatar_tensao(leitura.tensao))
        self.lblCorrenteValor.setText(formatar_corrente(leitura.corrente))
        self.lblPotenciaValor.setText(formatar_potencia(potencia))
        self.lblQualidade.setText(qualidade)
        self.lblQualidade.setStyleSheet(estilo_qualidade(qualidade))
        self.lblModoMedicao.setText(classificar_circuito(leitura))
        self._auditar_corrente(leitura)
        self._avaliar_risco(leitura, qualidade)

    # ------------------------------------------------------------------ gráfico: histórico
    def montar_painel_historico(self) -> None:
        self.painelHistorico = PainelHistorico(self.centralwidget)
        pos = self.conteudoLayout.indexOf(self.graficoConsumo)
        self.conteudoLayout.insertWidget(pos, self.painelHistorico)
        self.painelHistorico.consulta_solicitada.connect(self.consultar_historico)
        self.painelHistorico.tempo_real_solicitado.connect(self.voltar_ao_tempo_real)

    def consultar_historico(self, filtro: dict) -> None:
        if filtro["modo"] == "intervalo" and filtro["inicio"] >= filtro["fim"]:
            QMessageBox.warning(self, "Filtro inválido", "O início deve ser anterior ao fim.")
            return
        self._id_consulta += 1
        self.painelHistorico.definir_ocupado(True)
        self.pedir_historico.emit(self._id_consulta, filtro)  # SQLite roda na thread de banco

    def _historico_pronto(self, id_consulta: int, pontos) -> None:
        if id_consulta != self._id_consulta:
            return  # resposta de consulta já descartada
        self.painelHistorico.definir_ocupado(False)
        self._modo_historico = True
        self.painelHistorico.definir_modo(True, f"Modo: histórico ({len(pontos)} leituras)")
        self.lblTituloGrafico.setText("Histórico de Tensão (SQLite)")
        self._curva_tensao.setData([p[0] for p in pontos], [p[1] for p in pontos])
        if not pontos:
            self.statusBar().showMessage("Nenhuma leitura encontrada para o filtro.", 5000)

    def voltar_ao_tempo_real(self) -> None:
        self._id_consulta += 1
        self._modo_historico = False
        self.painelHistorico.definir_ocupado(False)
        self.painelHistorico.definir_modo(False, "Modo: tempo real")
        self.lblTituloGrafico.setText("Tendência de Tensão")
        self._curva_tensao.setData(self._historico_tempos, self._historico_tensoes)

    # ------------------------------------------------------------------ tabela / painel
    def preparar_tabela(self) -> None:
        self.tblEventos.setColumnCount(len(COLUNAS))
        self.tblEventos.setHorizontalHeaderLabels(COLUNAS)
        self.tblEventos.horizontalHeader().setStretchLastSection(True)
        self.tblEventos.verticalHeader().setVisible(False)  # a coluna ID já numera as linhas

    def preparar_modo_medicao(self) -> None:
        """O tipo de sinal (AC/DC) é escolhido pelo operador — não é auto-detectado
        nesta simulação — e decide qual garra (efetuador) o painel indica."""
        self.cmbTipoSinal.addItems(TIPOS_SINAL_DISPONIVEIS)

    # ------------------------------------------------------------------ Wi-Fi (thread)
    def _mostrar_wifi(self, texto: str, ativo: bool) -> None:
        self.lblStatusWifi.setText(texto)
        self.lblStatusWifi.setStyleSheet(estilo_status_conexao(ativo))
        vivo = self._wifi_worker is not None
        self.btnConectarWifi.setEnabled(not vivo)
        self.btnDesconectarWifi.setEnabled(vivo)

    def conectar_wifi(self) -> None:
        """Pede o endereço da sonda (pré-preenchido com o último usado) e conecta."""
        if self._wifi_worker is not None:
            return
        texto, ok = QInputDialog.getText(
            self, "Conectar à sonda (Wi-Fi)",
            "Endereço da sonda (host:porta).\n192.168.4.1:3333 = rede própria 'SkyVolt-Sonda'.",
            text=f"{self._wifi.host}:{self._wifi.porta}",
        )
        if not ok:
            return
        host, _, porta = texto.strip().rpartition(":")
        if not host or not porta.isdigit() or not 1 <= int(porta) <= 65535:
            log_warning(f"Entrada inválida bloqueada no endereço Wi-Fi: {texto!r}.")
            QMessageBox.warning(self, "Endereço inválido", "Use o formato host:porta, ex. 192.168.4.1:3333.")
            return
        self._wifi = ParametrosWifi(host=host, porta=int(porta))
        self._wifi_em_reconexao = False
        try:
            salvar_parametros_wifi(self._wifi)
        except OSError as erro:
            log_error(f"Falha ao salvar o endereço Wi-Fi em config.json: {erro}.")
        self.iniciar_wifi()

    def iniciar_wifi(self) -> None:
        if self._wifi_worker is not None:
            return
        worker = WifiWorker(
            host=self._wifi.host,
            porta=self._wifi.porta,
            intervalo_ms=self._config.intervalo_leitura_s * 1000,
            timeout_s=self.spnTimeout.value(),
            tipo_padrao=self.cmbTipoSinal.currentText(),
        )
        worker.estado_mudou.connect(lambda texto: self._mostrar_wifi(texto, False))
        worker.handshake_concluido.connect(self._wifi_handshake_ok)
        worker.leitura_recebida.connect(self.processar_leitura)
        worker.ack_recebido.connect(self._wifi_ack)
        worker.conexao_perdida.connect(self._wifi_perdida)
        worker.erro.connect(self._wifi_erro)
        worker.finished.connect(self._wifi_finalizada)
        worker.finished.connect(worker.deleteLater)
        self._wifi_worker = worker
        self._wifi_reconectar = True
        self._wifi_desconexao_manual = False
        self._mostrar_wifi(f"Conectando em {self._wifi.host}…", False)
        worker.start()

    def desconectar_wifi(self) -> None:
        self._wifi_reconectar = False
        self._wifi_em_reconexao = False
        self._wifi_desconexao_manual = True
        self._timer_reconexao_wifi.stop()
        self._timer_ack_rele.stop()
        if self._wifi_worker is not None:
            self._wifi_worker.solicitar_parada()
            self._mostrar_wifi("Desconectando…", False)
        else:
            self._mostrar_wifi("Desconectado", False)

    def _wifi_handshake_ok(self, destino: str) -> None:
        self._wifi_em_reconexao = False
        self._mostrar_wifi("Conectado", True)
        log_sucesso(f"Sonda Wi-Fi conectada em {destino}.")
        self.registrar_evento("Comunicação", f"Sonda Wi-Fi conectada em {destino}", "Info")
        # A sonda liga com K2 aberto: sincroniza com o estado do disjuntor gravado no banco.
        self._wifi_worker.enviar_comando(montar_comando_modo(self.cmbTipoSinal.currentText()))
        self._enviar_rele()

    def _enviar_rele(self) -> None:
        if self._wifi_worker is None:
            return
        self._rele_esperado = "FECHADO" if self._disjuntor_fechado else "ABERTO"
        self._wifi_worker.enviar_comando(montar_comando_rele(self._disjuntor_fechado))
        self._timer_ack_rele.start()

    def _wifi_ack(self, ack: dict) -> None:
        tipo = ack.get("ack")
        if tipo == "RELE" and ack.get("motivo") == "SOBRECORRENTE":
            self._disparo_sonda(ack)
        elif tipo == "RELE":
            if ack.get("estado") == self._rele_esperado:
                self._timer_ack_rele.stop()
            log_info(f"Sonda confirmou a chave K2 {ack.get('estado')}.")
        elif tipo == "MODO":
            log_info(f"Sonda em modo {ack.get('tipo')}.")
        elif tipo == "ERRO":
            log_error(f"Sonda recusou comando: {ack.get('motivo')}.")
            self.registrar_evento("Comunicação", f"Sonda recusou comando: {ack.get('motivo')}", "Alerta")

    def _disparo_sonda(self, ack: dict) -> None:
        """A sonda abriu o K2 sozinha por sobrecorrente: o disjuntor do app acompanha (com histórico)."""
        self._timer_ack_rele.stop()
        try:
            corrente = f"~{float(ack.get('i')):.1f} A"
        except (TypeError, ValueError):
            corrente = "corrente fora da escala"
        descricao = f"Disparo por sobrecorrente na sonda ({corrente}): chave K2 aberta"
        log_error(f"{descricao}.")
        self.statusBar().showMessage(f"{descricao}. Verifique se há carga em série antes de religar.", 15000)
        if self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False
        if self._disjuntor_fechado:
            self._comandar_disjuntor("ABERTO", descricao, "Critico")
        else:
            self.registrar_evento("Disjuntor", descricao, "Critico")

    def _rele_sem_ack(self) -> None:
        log_error(f"Sonda não confirmou a chave K2 {self._rele_esperado} em {TIMEOUT_ACK_RELE_MS / 1000:.0f}s.")
        self.registrar_evento(
            "Comunicação", f"Sonda não confirmou a chave K2 ({self._rele_esperado})", "Critico"
        )

    def _wifi_perdida(self, mensagem: str) -> None:
        log_error(f"Link Wi-Fi perdido: {mensagem}")
        self._timer_ack_rele.stop()
        self._wifi_em_reconexao = True
        self._mostrar_wifi("Link perdido — reconectando…", False)
        self.registrar_evento(
            "Comunicação", f"Link Wi-Fi perdido (a sonda abre a chave K2): {mensagem}", "Critico"
        )
        if self._wifi_reconectar:
            self._timer_reconexao_wifi.start()

    def _wifi_erro(self, mensagem: str) -> None:
        log_error(mensagem)
        self.statusBar().showMessage(mensagem, 10000)
        if self._wifi_em_reconexao and self._wifi_reconectar:
            self._mostrar_wifi("Link perdido — reconectando…", False)
            self._timer_reconexao_wifi.start()  # a sonda pode ainda estar reiniciando
            return
        self._wifi_reconectar = False
        self._mostrar_wifi("Falha na conexão", False)
        self.registrar_evento("Comunicação", mensagem, "Alerta")

    def _wifi_finalizada(self) -> None:
        self._wifi_worker = None
        if self._encerrando:
            return
        texto = "Desconectado" if self._wifi_desconexao_manual else self.lblStatusWifi.text()
        self._wifi_desconexao_manual = False
        self._mostrar_wifi(texto, False)

    def _tentar_reconectar_wifi(self) -> None:
        if self._wifi_reconectar and self._wifi_worker is None:
            self.iniciar_wifi()

    def adicionar_evento(self, evento: Evento) -> None:
        linha = self.tblEventos.rowCount()
        self.tblEventos.insertRow(linha)
        for coluna, valor in enumerate(evento_para_linha(evento)):
            self.tblEventos.setItem(linha, coluna, QTableWidgetItem(valor))

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

    # ------------------------------------------------------------------ disjuntor
    def _acionar_disjuntor_automatico(self) -> None:
        self._risco_ativo = False
        if not self._disjuntor_fechado:
            return  # operador já agiu manualmente nesse meio tempo
        self._comandar_disjuntor(
            "ABERTO",
            f"Corte automático — operador não reagiu em {self._config.tempo_reacao_s}s",
            "Critico",
            automatico=True,
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

    def _comandar_disjuntor(
        self, novo_status: str, descricao: str, severidade: str,
        simular_falha: bool = False, automatico: bool = False,
    ) -> None:
        """Pede à thread de banco o comando atômico (disjuntor + histórico)."""
        self.btnAlternarDisjuntor.setEnabled(False)  # evita duplo clique até a resposta
        self.pedir_comando_disjuntor.emit({
            "novo_status": novo_status, "descricao": descricao, "severidade": severidade,
            "simular_falha": simular_falha, "automatico": automatico,
        })

    def _comando_concluido(self, resultado, ctx) -> None:
        """Sincroniza a tela com o que ficou gravado no banco — inclusive após ROLLBACK."""
        self.btnAlternarDisjuntor.setEnabled(True)
        self._disjuntor_fechado = resultado.status_no_banco == "FECHADO"
        self.atualizar_disjuntor()

        if not resultado.sucesso:
            log_error(f"Falha na operação de corte emergencial. Rollback executado: {resultado.erro}.")
            QMessageBox.critical(
                self, "Transação revertida (ROLLBACK)",
                f"O comando falhou e foi desfeito por completo:\n{resultado.erro}\n\n"
                f"Disjuntor no banco: {resultado.status_no_banco}. Nenhum evento foi gravado.",
            )
            return

        self._enviar_rele()  # disjuntor do app -> chave K2 da sonda (se conectada por Wi-Fi)
        self.adicionar_evento(resultado.evento)
        self.tblEventos.scrollToBottom()
        log_evento("Disjuntor", ctx["descricao"], ctx["severidade"])
        if ctx["novo_status"] == "ABERTO":
            log_warning(f"Corte de carga executado: {ctx['descricao']}. Disjuntor ABERTO (COMMIT).")
        else:
            log_info(f"{ctx['descricao']}. Disjuntor FECHADO (COMMIT).")
        if ctx["automatico"]:
            QMessageBox.warning(
                self, "Corte automático",
                f"Risco não resolvido em {self._config.tempo_reacao_s}s — disjuntor aberto automaticamente.",
            )

    # ------------------------------------------------------------------ configurações
    def aplicar_config_drone(self) -> None:
        """Salva porta + baud alvo + timeout em config.json (valem na próxima conexão)."""
        self._serial.porta_com = self.cmbPortaCOM.currentText()
        self._serial.baud_rate = self.cmbBaudRate.currentText()
        self._serial.timeout_s = self.spnTimeout.value()
        porta, baud, timeout = self._serial.porta_com, self._serial.baud_rate, self._serial.timeout_s

        try:
            salvar_parametros_json(self._config, self._serial)
        except OSError as erro:
            log_error(f"Falha ao salvar a configuração serial em config.json: {erro}.")
            QMessageBox.critical(self, "Configuração serial", f"Não foi possível salvar config.json:\n{erro}")
            return

        log_info(f"Configuração serial salva: {porta} @ {baud} bps, timeout {timeout}s.")
        QMessageBox.information(
            self, "Configuração serial",
            f"Parâmetros salvos em config.json: {porta}, alvo {baud} bps (a conexão sempre "
            f"inicia a 9600), timeout {timeout}s. Valem na próxima conexão.",
        )

    def aplicar_configuracao(self) -> None:
        nova = abrir_configuracoes(self, self._config)
        if nova is None:
            return
        self._config = nova
        self.pedir_salvar_limites.emit(nova)  # SQLite na thread de banco
        try:
            salvar_parametros_json(self._config, self._serial)
        except OSError as erro:
            log_error(f"config.json não pôde ser atualizado: {erro}.")
        if not self._config.disjuntor_automatico and self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False
        log_sucesso("Configuração aplicada — novos limites em vigor.")
        QMessageBox.information(
            self, "Configuração aplicada",
            "Limites aplicados. O novo intervalo de leitura vale na próxima conexão.",
        )

    # ------------------------------------------------------------------ encerramento
    def closeEvent(self, event) -> None:
        """Encerramento cooperativo: pede parada à thread serial, espera, e só então
        encerra a thread de banco (o deleteLater dos workers roda no finished)."""
        self._encerrando = True
        self._reconectar = False
        self._wifi_reconectar = False
        self._timer_reconexao.stop()
        self._timer_reconexao_wifi.stop()
        self._timer_ack_rele.stop()
        for worker in (self._serial_worker, self._wifi_worker):
            if worker is not None:
                worker.solicitar_parada()
                worker.wait(3000)
        self._thread_db.quit()
        self._thread_db.wait(3000)
        super().closeEvent(event)


def criar_janela_principal() -> MainController:
    """Ponto de entrada usado por app/main.py."""
    return MainController()
