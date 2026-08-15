# Destino no GitHub (repo skyvolt-drone): app/controllers/main_controller.py
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from app.models.configuracao import ConfiguracaoSistema
from app.models.evento import COLUNAS, eventos_iniciais
from app.models.telemetria import SensorTelemetria
from app.ui.main_window_ui import Ui_MainWindow


class MainController(QMainWindow, Ui_MainWindow):
    def __init__(self, configuracao: Optional[ConfiguracaoSistema] = None) -> None:
        super().__init__()
        self.setupUi(self)

        self._config = configuracao or ConfiguracaoSistema()
        self._sensor = SensorTelemetria()
        self._eventos = eventos_iniciais()

        self._configurar_tabela_eventos()
        self._conectar_sinais()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._atualizar_leitura)
        self._timer.start(self._config.intervalo_leitura_s * 1000)

        self._atualizar_leitura()

    def _conectar_sinais(self) -> None:
        self.btnAlternarDisjuntor.clicked.connect(self._alternar_disjuntor)
        self.btnConfiguracoes.clicked.connect(self._abrir_configuracoes)

    def _configurar_tabela_eventos(self) -> None:
        self.tblEventos.setColumnCount(len(COLUNAS))
        self.tblEventos.setHorizontalHeaderLabels(COLUNAS)
        # TODO: popular linhas a partir de self._eventos (usar app.models.formatacao quando pronto)

    def _atualizar_leitura(self) -> None:
        leitura = self._sensor.proxima_leitura()
        # TODO: trocar por app.models.formatacao (formatar_tensao/corrente/potencia) quando pronto
        self.lblTensaoValor.setText(str(leitura.tensao))
        self.lblCorrenteValor.setText(str(leitura.corrente))
        self.lblPotenciaValor.setText(str(leitura.potencia))
        self.lblStatusDisjuntor.setText("Fechado" if leitura.disjuntor_fechado else "Aberto")

        dentro_da_faixa = self._config.esta_dentro_da_faixa(leitura.tensao, leitura.corrente)
        self.lblQualidade.setText("Normal" if dentro_da_faixa else "Fora da faixa")
        # TODO: atualizar self.graficoConsumo (PlotWidget) com o histórico de leituras

    def _alternar_disjuntor(self) -> None:
        self._sensor.alternar_disjuntor()
        self._atualizar_leitura()

    def _abrir_configuracoes(self) -> None:
        from app.controllers.config_controller import ConfigController

        dialogo = ConfigController(self._config, parent=self)
        if dialogo.exec_():
            self._config = dialogo.configuracao()
            self._timer.setInterval(self._config.intervalo_leitura_s * 1000)
