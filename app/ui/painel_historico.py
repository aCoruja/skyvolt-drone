from __future__ import annotations

from PyQt5.QtCore import QDateTime, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QDateTimeEdit, QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget

FORMATO = "yyyy-MM-dd HH:mm:ss"


class PainelHistorico(QWidget):
    """View pura: só widgets e sinais. Quem consulta o banco é o controller."""

    consulta_solicitada = pyqtSignal(dict)
    tempo_real_solicitado = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.lblModo = QLabel("Modo: tempo real")
        self.cmbFiltro = QComboBox()
        self.cmbFiltro.addItems(["Últimas N leituras", "Intervalo de datas"])
        self.spnN = QSpinBox()
        self.spnN.setRange(10, 100000)
        self.spnN.setValue(200)
        agora = QDateTime.currentDateTime()
        self.dtInicio = QDateTimeEdit(agora.addSecs(-3600))
        self.dtFim = QDateTimeEdit(agora)
        for dt in (self.dtInicio, self.dtFim):
            dt.setCalendarPopup(True)
            dt.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        self.btnConsultar = QPushButton("Consultar histórico")
        self.btnTempoReal = QPushButton("Voltar ao tempo real")
        self.btnTempoReal.setEnabled(False)

        for w in (self.lblModo, self.cmbFiltro, self.spnN, self.dtInicio, self.dtFim,
                  self.btnConsultar, self.btnTempoReal):
            lay.addWidget(w)
        lay.addStretch(1)

        self.cmbFiltro.currentIndexChanged.connect(self._alternar_campos)
        self.btnConsultar.clicked.connect(self._emitir_consulta)
        self.btnTempoReal.clicked.connect(self.tempo_real_solicitado)
        self._alternar_campos()

    def _alternar_campos(self) -> None:
        por_n = self.cmbFiltro.currentIndex() == 0
        self.spnN.setVisible(por_n)
        self.dtInicio.setVisible(not por_n)
        self.dtFim.setVisible(not por_n)

    def _emitir_consulta(self) -> None:
        if self.cmbFiltro.currentIndex() == 0:
            filtro = {"modo": "ultimas", "n": self.spnN.value()}
        else:
            filtro = {
                "modo": "intervalo",
                "inicio": self.dtInicio.dateTime().toString(FORMATO),
                "fim": self.dtFim.dateTime().toString(FORMATO),
            }
        self.consulta_solicitada.emit(filtro)

    def definir_ocupado(self, ocupado: bool) -> None:
        self.btnConsultar.setEnabled(not ocupado)

    def definir_modo(self, historico: bool, texto: str) -> None:
        self.lblModo.setText(texto)
        self.btnTempoReal.setEnabled(historico)
