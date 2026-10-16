from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget

from app.models.configuracao import (
    ConfiguracaoSistema,
    copiar_configuracao,
    validar_configuracao,
)
from app.models.logger_service import log_info, log_warning
from app.models.repositorios import RegrasLimitesRepository
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
        for spin in (self.spnTensaoMinAC, self.spnTensaoMaxAC):
            spin.setRange(0.0, 500.0)
            spin.setDecimals(1)
            spin.setSuffix(" V")

        for spin in (self.spnTensaoMinDC, self.spnTensaoMaxDC):
            spin.setRange(0.0, 150.0)
            spin.setDecimals(1)
            spin.setSuffix(" V")

        self.spnCorrenteMax.setRange(0.0, 300.0)
        self.spnCorrenteMax.setDecimals(2)
        self.spnCorrenteMax.setSuffix(" A")

        self.spnIntervalo.setRange(1.0, 3600.0)
        self.spnIntervalo.setDecimals(0)
        self.spnIntervalo.setSuffix(" s")

        self.spnTempoReacao.setRange(1, 300)
        self.spnTempoReacao.setSuffix(" s")

        self.chkDisjuntorAutomatico.toggled.connect(self.spnTempoReacao.setEnabled)

    def preencher_dialog(self) -> None:
        cfg = self._configuracao
        self.spnTensaoMinAC.setValue(cfg.tensao_minima_ac)
        self.spnTensaoMaxAC.setValue(cfg.tensao_maxima_ac)
        self.spnTensaoMinDC.setValue(cfg.tensao_minima_dc)
        self.spnTensaoMaxDC.setValue(cfg.tensao_maxima_dc)
        self.spnCorrenteMax.setValue(cfg.corrente_maxima)
        self.spnIntervalo.setValue(cfg.intervalo_leitura_s)
        self.cmbPeriodo.setCurrentText(cfg.periodo_historico)
        data_ini = cfg.data_inicio
        self.dateInicio.setDate(QDate(data_ini.year, data_ini.month, data_ini.day))

        self.chkDisjuntorAutomatico.setChecked(cfg.disjuntor_automatico)
        self.spnTempoReacao.setValue(cfg.tempo_reacao_s)
        self.spnTempoReacao.setEnabled(cfg.disjuntor_automatico)

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
        """Validação preventiva em tempo de execução para a demonstração prática."""
        nova_cfg = self.ler_dialog()
        erros = validar_configuracao(nova_cfg)

        if erros:
            log_warning(f"Entrada inválida barrada preventivamente no diálogo: {erros}")
            msg = "Falhas de validação encontradas:\n\n• " + "\n• ".join(erros)
            QMessageBox.warning(self, "Entrada Inválida", msg)
            return

        try:
            RegrasLimitesRepository.salvar(nova_cfg)
            self._configuracao = nova_cfg
            log_info("Novos limites operacionais persistidos na tabela regras_limites.")
            self.accept()
        except Exception as e:
            log_warning(f"Erro ao salvar limites no banco relacional: {e}")
            QMessageBox.critical(self, "Erro de Banco", f"Não foi possível salvar os limites:\n{e}")

    def configuracao(self) -> ConfiguracaoSistema:
        return self._configuracao


def abrir_configuracoes(
    parent: QWidget, configuracao: ConfiguracaoSistema
) -> Optional[ConfiguracaoSistema]:
    dialogo = ConfigController(configuracao, parent=parent)
    if dialogo.exec_():
        return dialogo.configuracao()
    return None
