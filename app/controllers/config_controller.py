# Destino no GitHub (repo skyvolt-drone): app/controllers/config_controller.py
from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from app.models.configuracao import ConfiguracaoSistema, copiar_configuracao, validar_configuracao
from app.ui.config_dialog_ui import Ui_ConfigDialog


class ConfigController(QDialog, Ui_ConfigDialog):
    def __init__(self, configuracao: ConfiguracaoSistema, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._configuracao = copiar_configuracao(configuracao)
        self._montar_dialog()
        self.preencher_dialog()

    def _montar_dialog(self) -> None:
        self.setupUi(self)
        self.cmbPeriodo.addItems(ConfiguracaoSistema.PERIODOS_DISPONIVEIS)
        self.buttonBox.accepted.connect(self._validar_e_aceitar)
        self.buttonBox.rejected.connect(self.reject)

    def preencher_dialog(self) -> None:
        configuracao = self._configuracao
        self.spnTensaoMin.setValue(configuracao.tensao_minima)
        self.spnTensaoMax.setValue(configuracao.tensao_maxima)
        self.spnCorrenteMax.setValue(configuracao.corrente_maxima)
        self.spnIntervalo.setValue(configuracao.intervalo_leitura_s)
        self.cmbPeriodo.setCurrentText(configuracao.periodo_historico)
        # TODO: self.dateInicio.setDate(...) a partir de configuracao.data_inicio (QDate.fromString)

    def ler_dialog(self) -> ConfiguracaoSistema:
        return ConfiguracaoSistema(
            tensao_minima=self.spnTensaoMin.value(),
            tensao_maxima=self.spnTensaoMax.value(),
            corrente_maxima=self.spnCorrenteMax.value(),
            intervalo_leitura_s=int(self.spnIntervalo.value()),
            periodo_historico=self.cmbPeriodo.currentText(),
            data_inicio=self.dateInicio.date().toPyDate(),
        )

    def _validar_e_aceitar(self) -> None:
        nova_configuracao = self.ler_dialog()
        erros = validar_configuracao(nova_configuracao)
        if erros:
            QMessageBox.warning(self, "Configuração inválida", "\n".join(erros))
            return
        self._configuracao = nova_configuracao
        self.accept()

    def configuracao(self) -> ConfiguracaoSistema:
        return self._configuracao


def abrir_configuracoes(parent: QWidget, configuracao: ConfiguracaoSistema) -> Optional[ConfiguracaoSistema]:
    """Abre o dialog de configuração modal. Retorna a nova ConfiguracaoSistema
    se o usuário confirmar, ou None se cancelar."""
    dialogo = ConfigController(configuracao, parent=parent)
    if dialogo.exec_():
        return dialogo.configuracao()
    return None
