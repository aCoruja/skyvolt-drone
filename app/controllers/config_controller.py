# Destino no GitHub (repo skyvolt-drone): app/controllers/config_controller.py
from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from app.models.configuracao import ConfiguracaoSistema
from app.ui.config_dialog_ui import Ui_ConfigDialog


class ConfigController(QDialog, Ui_ConfigDialog):
    def __init__(self, configuracao: ConfiguracaoSistema, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self._configuracao = configuracao
        self._carregar_valores(configuracao)

        self.buttonBox.accepted.connect(self._validar_e_aceitar)
        self.buttonBox.rejected.connect(self.reject)

    def _carregar_valores(self, configuracao: ConfiguracaoSistema) -> None:
        self.spnTensaoMin.setValue(configuracao.tensao_minima)
        self.spnTensaoMax.setValue(configuracao.tensao_maxima)
        self.spnCorrenteMax.setValue(configuracao.corrente_maxima)
        self.spnIntervalo.setValue(configuracao.intervalo_leitura_s)
        self.cmbPeriodo.addItems(ConfiguracaoSistema.PERIODOS_DISPONIVEIS)
        self.cmbPeriodo.setCurrentText(configuracao.periodo_historico)
        # TODO: self.dateInicio.setDate(...) a partir de configuracao.data_inicio (QDate.fromString)

    def _validar_e_aceitar(self) -> None:
        try:
            nova_configuracao = ConfiguracaoSistema(
                tensao_minima=self.spnTensaoMin.value(),
                tensao_maxima=self.spnTensaoMax.value(),
                corrente_maxima=self.spnCorrenteMax.value(),
                intervalo_leitura_s=int(self.spnIntervalo.value()),
                periodo_historico=self.cmbPeriodo.currentText(),
                data_inicio=self.dateInicio.date().toPyDate(),
            )
        except ValueError as erro:
            QMessageBox.warning(self, "Configuração inválida", str(erro))
            return

        self._configuracao = nova_configuracao
        self.accept()

    def configuracao(self) -> ConfiguracaoSistema:
        return self._configuracao
