# Destino no GitHub (repo skyvolt-drone): app/controllers/main_controller.py
from __future__ import annotations

from datetime import datetime, timedelta

import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem

from app.controllers.config_controller import abrir_configuracoes
from app.models.configuracao import configuracao_padrao
from app.models.dados_simulados import gerar_curva_consumo
from app.models.evento import COLUNAS, Evento, criar_evento, eventos_iniciais, evento_para_linha
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
        self._config = configuracao_padrao()
        self._disjuntor_fechado = True
        self._eventos: list[Evento] = eventos_iniciais()

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
        for evento in self._eventos:
            self.adicionar_evento(evento)

    def preparar_modo_medicao(self) -> None:
        """O tipo de sinal (AC/DC) é escolhido pelo operador — não é auto-detectado
        nesta simulação — e decide qual garra (efetuador) o painel indica."""
        self.cmbTipoSinal.addItems(TIPOS_SINAL_DISPONIVEIS)

    def preparar_conectividade(self) -> None:
        """Três canais distintos, conforme a arquitetura de comunicação do documento
        técnico (docs/SkyVolt_Documento.tex, Seção 4.3): LoRa apenas recebe a
        telemetria de tensão/corrente/potência; WiFi carrega vídeo/comandos de voo
        (FPV); a porta COM — com seu baud rate e timeout — serve apenas para
        configuração local do drone, não para operação contínua. Nesta etapa A1/1
        as três só alteram o status visual — sem hardware real."""
        self.atualizar_status_lora(conectado=False)
        self.atualizar_status_wifi(conectado=False)

        self.cmbPortaCOM.addItems(PORTAS_COM_DISPONIVEIS)
        self.cmbBaudRate.addItems(BAUD_RATES_DISPONIVEIS)
        self.spnTimeout.setRange(1, 60)
        self.spnTimeout.setValue(5)
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
        porta, baud, timeout = (
            self.cmbPortaCOM.currentText(),
            self.cmbBaudRate.currentText(),
            self.spnTimeout.value(),
        )
        log_sucesso(f"Configuração do drone aplicada via {porta} @ {baud} bps, timeout {timeout}s.")
        QMessageBox.information(
            self,
            "Configuração do drone",
            f"Parâmetros enviados ao drone pela porta {porta} ({baud} bps, timeout {timeout}s).",
        )

    def adicionar_evento(self, evento: Evento) -> None:
        linha = self.tblEventos.rowCount()
        self.tblEventos.insertRow(linha)
        for coluna, valor in enumerate(evento_para_linha(evento)):
            self.tblEventos.setItem(linha, coluna, QTableWidgetItem(valor))

    def registrar_evento(self, tipo: str, descricao: str, severidade: str) -> None:
        """Registra um evento em tempo real: adiciona linha na tabela de histórico
        e ecoa no console (colorido conforme a severidade)."""
        self.adicionar_evento(criar_evento(tipo=tipo, descricao=descricao, severidade=severidade))
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

        self._avaliar_risco(leitura, qualidade)

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
        motivo = "corrente alta" if corrente_excedida(leitura, self._config) else "tensão fora da faixa"
        self.registrar_evento(
            tipo="Risco",
            descricao=(
                f"Risco detectado ({motivo}) — corte automático em "
                f"{self._config.tempo_reacao_s}s se não houver ação manual"
            ),
            severidade="Alerta",
        )

    def _acionar_disjuntor_automatico(self) -> None:
        self._risco_ativo = False
        if not self._disjuntor_fechado:
            return  # operador já agiu manualmente nesse meio tempo

        self._disjuntor_fechado = False
        self.atualizar_disjuntor()
        self.registrar_evento(
            tipo="Disjuntor",
            descricao=f"Corte automático — operador não reagiu em {self._config.tempo_reacao_s}s",
            severidade="Critico",
        )
        QMessageBox.warning(
            self,
            "Corte automático",
            f"Risco não resolvido em {self._config.tempo_reacao_s}s — disjuntor aberto automaticamente.",
        )

    def atualizar_disjuntor(self) -> None:
        self.lblStatusDisjuntor.setText(texto_status_disjuntor(self._disjuntor_fechado))
        self.lblStatusDisjuntor.setStyleSheet(estilo_status_disjuntor(self._disjuntor_fechado))

    def alternar_disjuntor(self) -> None:
        if self._disjuntor_fechado:
            resposta = QMessageBox.question(
                self,
                "Confirmar corte de emergência",
                "Tem certeza que deseja abrir o disjuntor e cortar o fornecimento de energia?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resposta != QMessageBox.Yes:
                return

        if self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False

        self._disjuntor_fechado = not self._disjuntor_fechado
        self.atualizar_disjuntor()

        if self._disjuntor_fechado:
            descricao, severidade = "Comando de fechamento do disjuntor", "Info"
        else:
            descricao, severidade = "Comando de abertura do disjuntor", "Critico"
        self.registrar_evento(tipo="Disjuntor", descricao=descricao, severidade=severidade)

        self.atualizar_telemetria()

    def aplicar_configuracao(self) -> None:
        nova_configuracao = abrir_configuracoes(self, self._config)
        if nova_configuracao is None:
            return
        self._config = nova_configuracao
        self._timer.setInterval(self._config.intervalo_leitura_s * 1000)
        if not self._config.disjuntor_automatico and self._risco_ativo:
            self._timer_risco.stop()
            self._risco_ativo = False
        log_sucesso("Configuração aplicada — novos limites e intervalo de leitura em vigor.")
        QMessageBox.information(
            self, "Configuração aplicada", "Os novos parâmetros foram aplicados com sucesso."
        )


def criar_janela_principal() -> MainController:
    """Ponto de entrada usado por app/main.py."""
    return MainController()
