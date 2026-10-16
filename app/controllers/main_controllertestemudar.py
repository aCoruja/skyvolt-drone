from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem

from app.controllers.config_controller import abrir_configuracoes
from app.database.connection import Database
from app.models.configuracao import (
    ConfiguracaoSistema,
    carregar_parametros_json,
    salvar_parametros_json,
)
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
from app.models.logger_service import log_error, log_info, log_warning
from app.models.repositorios import (
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
        """Carrega os dados persistidos na QTableWidget no evento showEvent."""
        super().showEvent(event)
        self.carregar_eventos_do_banco()

    def montar_janela(self) -> None:
        self.setupUi(self)
        self.criar_estado()
        self.carregar_grafico()
        self.preparar_tabela()
        self.preparar_modo_medicao()
        self.preparar_conectividade()

        # Conexão de Sinais e Slots
        self.btnAlternarDisjuntor.clicked.connect(self.alternar_disjuntor)
        self.btnConfiguracoes.clicked.connect(self.aplicar_configuracao)
        self.cmbTipoSinal.currentTextChanged.connect(self.atualizar_telemetria)
        self._timer_risco.timeout.connect(self._acionar_disjuntor_automatico)
        self.btnConectar.clicked.connect(self.conectar_lora)
        self.btnDesconectar.clicked.connect(self.desconectar_lora)
        self.btnConectarWifi.clicked.connect(self.conectar_wifi)
        self.btnDesconectarWifi.clicked.connect(self.desconectar_wifi)
        self.btnAplicarConfigDrone.clicked.connect(self.aplicar_config_drone)

        # Loop de telemetria contínua
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.atualizar_telemetria)
        self._timer.start(self._config.intervalo_leitura_s * 1000)

        self.atualizar_telemetria()
        self.atualizar_disjuntor_ui()

    def criar_estado(self) -> None:
        # 1. Carrega parâmetros estruturados do config.json
        self._config, self._serial = carregar_parametros_json()

        # 2. Sincroniza com o banco SQLite caso já existam limites salvos
        limites_banco = RegrasLimitesRepository.carregar()
        if limites_banco is not None:
            self._config = limites_banco

        # 3. Consulta estado real persistido do disjuntor principal
        status_disj = DispositivoRepository.obter_status("DISJ_PRINCIPAL")
        self._disjuntor_fechado = (status_disj == "FECHADO")

        self._risco_ativo = False
        self._timer_risco = QTimer(self)
        self._timer_risco.setSingleShot(True)

        # Histórico inicial para renderização visual do gráfico
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
        self.carregar_eventos_do_banco()

    def carregar_eventos_do_banco(self) -> None:
        """Carrega dinamicamente a tabela a partir do banco de dados relacional."""
        eventos = EventoRepository.listar_todos()
        self.tblEventos.setRowCount(0)
        for evento in reversed(eventos):
            self._adicionar_linha_tabela(evento)

    def _adicionar_linha_tabela(self, evento: Evento) -> None:
        linha = self.tblEventos.rowCount()
        self.tblEventos.insertRow(linha)
        for coluna, valor in enumerate(evento_para_linha(evento)):
            self.tblEventos.setItem(linha, coluna, QTableWidgetItem(valor))
        self.tblEventos.scrollToBottom()

    def registrar_evento(
        self, tipo: str, descricao: str, severidade: str, valor_medido: Optional[float] = None
    ) -> None:
        """Grava imediatamente o evento no SQLite e atualiza a QTableWidget."""
        evento = criar_evento(tipo, descricao, severidade, valor_medido)
        try:
            novo_id = EventoRepository.inserir(evento)
            evento.id = novo_id
            self._adicionar_linha_tabela(evento)

            if severidade == "Critico":
                log_error(f"{tipo}: {descricao}")
            elif severidade == "Alerta":
                log_warning(f"{tipo}: {descricao}")
            else:
                log_info(f"{tipo}: {descricao}")
        except Exception as e:
            log_error(f"Erro ao persistir evento no banco relacional: {e}")

    def preparar_modo_medicao(self) -> None:
        self.cmbTipoSinal.addItems(TIPOS_SINAL_DISPONIVEIS)

    def preparar_conectividade(self) -> None:
        self.atualizar_status_lora(conectado=False)
        self.atualizar_status_wifi(conectado=False)

        self.cmbPortaCOM.addItems(PORTAS_COM_DISPONIVEIS)
        self.cmbPortaCOM.setCurrentText(self._serial.porta_com)

        self.cmbBaudRate.addItems(BAUD_RATES_DISPONIVEIS)
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
        log_info("Link LoRa conectado (simulado) — recepção de telemetria ativa.")

    def desconectar_lora(self) -> None:
        self.atualizar_status_lora(conectado=False)
        log_info("Link LoRa desconectado.")

    def atualizar_status_wifi(self, conectado: bool) -> None:
        self.lblStatusWifi.setText(texto_status_conexao(conectado))
        self.lblStatusWifi.setStyleSheet(estilo_status_conexao(conectado))
        self.btnConectarWifi.setEnabled(not conectado)
        self.btnDesconectarWifi.setEnabled(conectado)

    def conectar_wifi(self) -> None:
        self.atualizar_status_wifi(conectado=True)
        log_info("Link WiFi conectado (simulado) — vídeo/comandos FPV ativos.")

    def desconectar_wifi(self) -> None:
        self.atualizar_status_wifi(conectado=False)
        log_info("Link WiFi desconectado.")

    def aplicar_config_drone(self) -> None:
        """Salva parâmetros de comunicação serial em config.json."""
        self._serial.porta_com = self.cmbPortaCOM.currentText()
        self._serial.baud_rate = self.cmbBaudRate.currentText()
        self._serial.timeout_s = self.spnTimeout.value()

        salvar_parametros_json(self._config, self._serial)
        log_info(
            f"Configuração serial persistida: {self._serial.porta_com} @ {self._serial.baud_rate} bps."
        )
        QMessageBox.information(
            self,
            "Configuração Serial",
            f"Parâmetros salvos em config.json:\nPorta: {self._serial.porta_com}\nBaud: {self._serial.baud_rate}",
        )

    def atualizar_telemetria(self) -> None:
        leitura = ler_telemetria(
            tipo_sinal=self.cmbTipoSinal.currentText(),
            disjuntor_fechado=self._disjuntor_fechado,
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

        # Registro no formato exato solicitado pelo edital:
        # [WARNING] Limite de corrente violado: 28.5A (Limite configurado: 25.0A).
        if self._disjuntor_fechado and corrente_excedida(leitura, self._config):
            log_warning(
                f"Limite de corrente violado: {leitura.corrente:.1f}A "
                f"(Limite configurado: {self._config.corrente_maxima:.1f}A)."
            )

        self._avaliar_risco(leitura, qualidade)

    def _avaliar_risco(self, leitura: LeituraTelemetria, qualidade: str) -> None:
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
        motivo = (
            "corrente alta"
            if corrente_excedida(leitura, self._config)
            else "tensão fora da faixa"
        )
        self.registrar_evento(
            tipo="Alarme",
            descricao=f"Risco detectado ({motivo}) — corte automático em {self._config.tempo_reacao_s}s",
            severidade="Alerta",
            valor_medido=leitura.corrente,
        )

    def _acionar_disjuntor_automatico(self) -> None:
        self._risco_ativo = False
        if not self._disjuntor_fechado:
            return

        sucesso = self._executar_corte_transacional(
            novo_status="ABERTO",
            descricao_evento=f"Corte automático — operador não reagiu em {self._config.tempo_reacao_s}s",
            severidade="Critico",
            simular_falha=False,
        )
        if sucesso:
            self._disjuntor_fechado = False
            self.atualizar_disjuntor_ui()
            QMessageBox.warning(
                self,
                "Corte Automático",
                f"Risco não solucionado em {self._config.tempo_reacao_s}s — disjuntor aberto automaticamente.",
            )

    def atualizar_disjuntor_ui(self) -> None:
        self.lblStatusDisjuntor.setText(texto_status_disjuntor(self._disjuntor_fechado))
        self.lblStatusDisjuntor.setStyleSheet(
            estilo_status_disjuntor(self._disjuntor_fechado)
        )

    def alternar_disjuntor(self) -> None:
        """Ação de corte emergencial. Possui botão dedicado para simular a falha
        transacional e demonstrar ao vivo o ROLLBACK exigido no edital."""
        novo_status = "ABERTO" if self._disjuntor_fechado else "FECHADO"

        if self._disjuntor_fechado:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Confirmação de Corte Emergencial")
            msg_box.setText("Selecione a ação para o disjuntor principal:")
            btn_normal = msg_box.addButton("Corte Emergencial (Normal)", QMessageBox.YesRole)
            btn_falha = msg_box.addButton("Simular Falha Transacional (Teste Rollback)", QMessageBox.ActionRole)
            btn_cancela = msg_box.addButton("Cancelar", QMessageBox.RejectRole)
            msg_box.exec_()

            if msg_box.clickedButton() == btn_cancela:
                return

            simular_falha = (msg_box.clickedButton() == btn_falha)
            descricao = "Comando de corte emergencial"
            severidade = "Critico"
        else:
            resp = QMessageBox.question(
                self,
                "Fechar Disjuntor",
                "Deseja restabelecer o fornecimento elétrico e fechar o disjuntor?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
            simular_falha = False
            descricao = "Comando de fechamento do disjuntor"
            severidade = "Info"

        if self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False

        sucesso = self._executar_corte_transacional(
            novo_status=novo_status,
            descricao_evento=descricao,
            severidade=severidade,
            simular_falha=simular_falha,
        )

        if sucesso:
            self._disjuntor_fechado = (novo_status == "FECHADO")
            self.atualizar_disjuntor_ui()
            self.atualizar_telemetria()

    def _executar_corte_transacional(
        self,
        novo_status: str,
        descricao_evento: str,
        severidade: str,
        simular_falha: bool = False,
    ) -> bool:
        """Controle transacional ACID com 'with conn:' na rotina de corte emergencial.
        Garante integridade 'tudo ou nada' (atualização do disjuntor + histórico).
        Em caso de interrupção, o SQLite executa ROLLBACK automaticamente."""
        conn = Database.get_connection()
        try:
            with conn:
                cursor = conn.cursor()

                # 1. Atualização do disjuntor
                cursor.execute(
                    """
                    UPDATE dispositivos
                    SET status = ?, ultima_atualizacao = datetime('now', 'localtime')
                    WHERE tag = 'DISJ_PRINCIPAL';
                    """,
                    (novo_status,),
                )

                # Interrupção forçada provocada para a demonstração da arguição técnica
                if simular_falha:
                    raise RuntimeError("Falha provocada na transação entre atuador e histórico")

                # 2. Inserção do evento correspondente
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao, severidade)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (agora, "Disjuntor", None, descricao_evento, severidade),
                )

            # Transação confirmada com sucesso (COMMIT automático pelo with conn:)
            conn.close()
            self.carregar_eventos_do_banco()
            log_info("Transação de corte/religamento confirmada no SQLite (COMMIT).")
            return True

        except Exception as e:
            # O 'with conn:' desfaz todas as alterações pendentes via ROLLBACK
            conn.close()
            # Formato estrito exigido pelo edital:
            # [ERROR] Falha na operação de corte emergencial. Rollback executado: <motivo>.
            log_error(f"Falha na operação de corte emergencial. Rollback executado: {e}.")
            QMessageBox.critical(
                self,
                "Transação Revertida (ROLLBACK)",
                f"Erro durante a transação!\n\n"
                f"Rollback executado com sucesso: {e}\n\n"
                f"O estado do disjuntor no banco SQLite permaneceu intacto e consistente.",
            )
            return False

    def aplicar_configuracao(self) -> None:
        nova_cfg = abrir_configuracoes(self, self._config)
        if nova_cfg is None:
            return

        self._config = nova_cfg
        salvar_parametros_json(self._config, self._serial)
        self._timer.setInterval(self._config.intervalo_leitura_s * 1000)

        if not self._config.disjuntor_automatico and self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False

        log_info("Configurações atualizadas no SQLite e sincronizadas no config.json.")
        QMessageBox.information(
            self, "Configurações", "Parâmetros atualizados e persistidos com sucesso."
        )


def criar_janela_principal() -> MainController:
    return MainController()
