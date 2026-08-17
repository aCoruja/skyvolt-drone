# Destino no GitHub (repo skyvolt-drone): app/controllers/config_controller.py
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from app.models.configuracao import ConfiguracaoSistema, copiar_configuracao, validar_configuracao
from app.ui.config_dialog_ui import Ui_ConfigDialog


class ConfigController(QDialog, Ui_ConfigDialog):
    def __init__(self, configuracao: ConfiguracaoSistema, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._configuracao = copiar_configuracao(configuracao)
        self._montar_dialog()
        self.preencher_dialog()

    def _montar_dialog(self) -> None:
        self.setupUi(self)
        self._configurar_spinboxes()
        self.cmbPeriodo.addItems(ConfiguracaoSistema.PERIODOS_DISPONIVEIS)
        self.buttonBox.accepted.connect(self._validar_e_aceitar)
        self.buttonBox.rejected.connect(self.reject)

    def _configurar_spinboxes(self) -> None:
        """Define faixa/casas decimais/sufixo de cada spin box — o Qt Designer não define
        isso, então sem isto os campos nascem limitados a 0,00–99,99 (padrão do PyQt) e
        travam silenciosamente valores como tensao_maxima_ac=242.0 em 99,99."""
        for spin in (self.spnTensaoMinAC, self.spnTensaoMaxAC):
            spin.setRange(0.0, 400.0)
            spin.setDecimals(1)
            spin.setSuffix(" V")

        for spin in (self.spnTensaoMinDC, self.spnTensaoMaxDC):
            spin.setRange(0.0, 100.0)
            spin.setDecimals(1)
            spin.setSuffix(" V")

        self.spnCorrenteMax.setRange(0.0, 200.0)
        self.spnCorrenteMax.setDecimals(2)
        self.spnCorrenteMax.setSuffix(" A")

        self.spnIntervalo.setRange(1.0, 3600.0)
        self.spnIntervalo.setDecimals(0)
        self.spnIntervalo.setSuffix(" s")

        self.spnTempoReacao.setRange(1, 300)
        self.spnTempoReacao.setSuffix(" s")

        self.chkDisjuntorAutomatico.toggled.connect(self.spnTempoReacao.setEnabled)

    def preencher_dialog(self) -> None:
        configuracao = self._configuracao
        self.spnTensaoMinAC.setValue(configuracao.tensao_minima_ac)
        self.spnTensaoMaxAC.setValue(configuracao.tensao_maxima_ac)
        self.spnTensaoMinDC.setValue(configuracao.tensao_minima_dc)
        self.spnTensaoMaxDC.setValue(configuracao.tensao_maxima_dc)
        self.spnCorrenteMax.setValue(configuracao.corrente_maxima)
        self.spnIntervalo.setValue(configuracao.intervalo_leitura_s)
        self.cmbPeriodo.setCurrentText(configuracao.periodo_historico)
        data_inicio = configuracao.data_inicio
        self.dateInicio.setDate(QDate(data_inicio.year, data_inicio.month, data_inicio.day))

        self.chkDisjuntorAutomatico.setChecked(configuracao.disjuntor_automatico)
        self.spnTempoReacao.setValue(configuracao.tempo_reacao_s)
        self.spnTempoReacao.setEnabled(configuracao.disjuntor_automatico)

    def ler_dialog(self) -> ConfiguracaoSistema:
        return ConfiguracaoSistema(
            tensao_minima_ac=self.spnTensaoMinAC.value(),
            tensao_maxima_ac=self.spnTensaoMaxAC.value(),
            tensao_minima_dc=self.spnTensaoMinDC.value(),
            tensao_maxima_dc=self.spnTensaoMaxDC.value(),
            corrente_maxima=self.spnCorrenteMax.value(),
            disjuntor_automatico=self.chkDisjuntorAutomatico.isChecked(),
            tempo_reacao_s=self.spnTempoReacao.value(),
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
