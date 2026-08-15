# Destino no GitHub (repo skyvolt-drone): app/controllers/main_controller.py
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem

from app.controllers.config_controller import abrir_configuracoes
from app.models.configuracao import configuracao_padrao
from app.models.evento import COLUNAS, Evento, eventos_iniciais, evento_para_linha
from app.models.telemetria import avaliar_qualidade, calcular_potencia, corrente_excedida, ler_telemetria
from app.ui.main_window_ui import Ui_MainWindow


class MainController(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.montar_janela()

    def montar_janela(self) -> None:
        self.setupUi(self)
        self.criar_estado()
        self.carregar_grafico()
        self.preparar_tabela()

        self.btnAlternarDisjuntor.clicked.connect(self.alternar_disjuntor)
        self.btnConfiguracoes.clicked.connect(self.aplicar_configuracao)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.atualizar_telemetria)
        self._timer.start(self._config.intervalo_leitura_s * 1000)

        self.atualizar_telemetria()
        self.atualizar_disjuntor()

    def criar_estado(self) -> None:
        self._config = configuracao_padrao()
        self._disjuntor_fechado = True
        self._eventos: list[Evento] = eventos_iniciais()

    def carregar_grafico(self) -> None:
        self.graficoConsumo.setBackground("w")
        self.graficoConsumo.setLabel("left", "Tensão (V)")
        self.graficoConsumo.setLabel("bottom", "Hora")
        self.graficoConsumo.showGrid(x=True, y=True)

    def preparar_tabela(self) -> None:
        self.tblEventos.setColumnCount(len(COLUNAS))
        self.tblEventos.setHorizontalHeaderLabels(COLUNAS)
        for evento in self._eventos:
            self.adicionar_evento(evento)

    def adicionar_evento(self, evento: Evento) -> None:
        linha = self.tblEventos.rowCount()
        self.tblEventos.insertRow(linha)
        for coluna, valor in enumerate(evento_para_linha(evento)):
            self.tblEventos.setItem(linha, coluna, QTableWidgetItem(valor))

    def atualizar_telemetria(self) -> None:
        leitura = ler_telemetria(disjuntor_fechado=self._disjuntor_fechado)
        potencia = calcular_potencia(leitura)

        # TODO: trocar por app.models.formatacao (formatar_tensao/corrente/potencia) quando pronto
        self.lblTensaoValor.setText(str(leitura.tensao))
        self.lblCorrenteValor.setText(str(leitura.corrente))
        self.lblPotenciaValor.setText(str(potencia))
        self.lblQualidade.setText(avaliar_qualidade(leitura, self._config))
        # TODO: atualizar self.graficoConsumo (PlotWidget) com o histórico de leituras

        if self._disjuntor_fechado and corrente_excedida(leitura, self._config):
            self._disjuntor_fechado = False
            self.atualizar_disjuntor()

    def atualizar_disjuntor(self) -> None:
        if self._disjuntor_fechado:
            self.lblStatusDisjuntor.setText("Fechado")
            self.lblStatusDisjuntor.setStyleSheet("color: green;")
        else:
            self.lblStatusDisjuntor.setText("Aberto")
            self.lblStatusDisjuntor.setStyleSheet("color: red;")

    def alternar_disjuntor(self) -> None:
        self._disjuntor_fechado = not self._disjuntor_fechado
        self.atualizar_disjuntor()
        self.atualizar_telemetria()

    def aplicar_configuracao(self) -> None:
        nova_configuracao = abrir_configuracoes(self, self._config)
        if nova_configuracao is None:
            return
        self._config = nova_configuracao
        self._timer.setInterval(self._config.intervalo_leitura_s * 1000)
        QMessageBox.information(
            self, "Configuração aplicada", "Os novos parâmetros foram aplicados com sucesso."
        )


def criar_janela_principal() -> MainController:
    """Ponto de entrada usado por app/main.py."""
    return MainController()
