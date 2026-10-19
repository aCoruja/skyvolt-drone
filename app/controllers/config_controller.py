from __future__ import annotations

import sqlite3
from typing import Optional

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QAbstractSpinBox, QDialog, QMessageBox, QWidget

from app.models.configuracao import ConfiguracaoSistema, copiar_configuracao, validar_configuracao
from app.models.logger_service import log_error, log_info, log_warning
from app.models.repositorios import RegrasLimitesRepository
from app.ui.config_dialog_ui import Ui_ConfigDialog

# Faixa ampla de propósito: o spin box aceita digitar negativos e a validação de
# models/configuracao.py é quem barra, com mensagem explicando o motivo.
FAIXA_DIGITAVEL = (-9999.0, 9999.0)


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

    def _campos_numericos(self) -> dict[str, QAbstractSpinBox]:
        return {
            "Tensão mínima AC": self.spnTensaoMinAC,
            "Tensão máxima AC": self.spnTensaoMaxAC,
            "Tensão mínima DC": self.spnTensaoMinDC,
            "Tensão máxima DC": self.spnTensaoMaxDC,
            "Corrente máxima": self.spnCorrenteMax,
            "Intervalo de leitura": self.spnIntervalo,
            "Tempo de reação": self.spnTempoReacao,
        }

    def _configurar_spinboxes(self) -> None:
        """Define faixa/casas decimais/sufixo de cada spin box — sem isso o PyQt limita
        os campos a 0,00–99,99 e trava silenciosamente valores como 242,0 V."""
        for spin in (self.spnTensaoMinAC, self.spnTensaoMaxAC, self.spnTensaoMinDC, self.spnTensaoMaxDC):
            spin.setRange(*FAIXA_DIGITAVEL)
            spin.setDecimals(1)
            spin.setSuffix(" V")

        self.spnCorrenteMax.setRange(*FAIXA_DIGITAVEL)
        self.spnCorrenteMax.setDecimals(2)
        self.spnCorrenteMax.setSuffix(" A")

        self.spnIntervalo.setRange(*FAIXA_DIGITAVEL)
        self.spnIntervalo.setDecimals(0)
        self.spnIntervalo.setSuffix(" s")

        self.spnTempoReacao.setRange(int(FAIXA_DIGITAVEL[0]), int(FAIXA_DIGITAVEL[1]))
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

    def _erros_de_preenchimento(self) -> list[str]:
        """Campos vazios ou com texto que não é número. O spin box guarda o último valor
        válido em value(), então é preciso conferir o texto digitado (cleanText)."""
        erros: list[str] = []
        for nome, spin in self._campos_numericos().items():
            texto = spin.cleanText().strip()
            if not texto:
                erros.append(f"{nome}: campo vazio.")
                continue
            try:
                float(texto.replace(".", "").replace(",", "."))
            except ValueError:
                erros.append(f"{nome}: '{texto}' não é um número.")
        return erros

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
        """Validação preventiva: nada é gravado enquanto houver erro de entrada."""
        erros = self._erros_de_preenchimento()
        nova_cfg = None
        if not erros:
            nova_cfg = self.ler_dialog()
            erros = validar_configuracao(nova_cfg)

        if erros:
            log_warning(f"Entrada inválida bloqueada no diálogo de limites: {'; '.join(erros)}")
            QMessageBox.warning(
                self, "Entrada inválida", "Corrija os campos abaixo:\n\n• " + "\n• ".join(erros)
            )
            return

        try:
            RegrasLimitesRepository.salvar(nova_cfg)
        except sqlite3.Error as erro:
            log_error(f"Falha ao gravar limites na tabela regras_limites. Rollback executado: {erro}.")
            QMessageBox.critical(self, "Erro de banco", f"Não foi possível salvar os limites:\n{erro}")
            return

        self._configuracao = nova_cfg
        log_info(
            f"Limites salvos no SQLite: corrente máx. {nova_cfg.corrente_maxima:.1f}A, "
            f"AC {nova_cfg.tensao_minima_ac:.1f}–{nova_cfg.tensao_maxima_ac:.1f}V, "
            f"DC {nova_cfg.tensao_minima_dc:.1f}–{nova_cfg.tensao_maxima_dc:.1f}V."
        )
        self.accept()

    def configuracao(self) -> ConfiguracaoSistema:
        return self._configuracao


def abrir_configuracoes(parent: QWidget, configuracao: ConfiguracaoSistema) -> Optional[ConfiguracaoSistema]:
    """Abre o dialog de configuração modal. Retorna a nova ConfiguracaoSistema
    (já gravada no banco) se o usuário confirmar, ou None se cancelar."""
    dialogo = ConfigController(configuracao, parent=parent)
    if dialogo.exec_():
        return dialogo.configuracao()
    return None
