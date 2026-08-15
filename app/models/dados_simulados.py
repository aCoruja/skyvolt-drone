from __future__ import annotations

# Stub — assinatura travada (Trello #10, responsável: Vitoria).
# NÃO alterar nome nem retorno: o controller já depende desta assinatura.


def gerar_curva_consumo(pontos: int = 24) -> tuple[list[float], list[float], list[float]]:
    """Gera (horas, tensoes, correntes) para alimentar o gráfico de consumo.

    TODO(Vitoria): tensão oscilando +-3% em torno de 220 V; corrente com
    perfil de carga (pico entre 18h e 21h). Testável no Colab com matplotlib
    antes de commitar.
    """
    horas: list[float] = []
    tensoes: list[float] = []
    correntes: list[float] = []
    # TODO: preencher horas, tensoes, correntes com `pontos` amostras
    return horas, tensoes, correntes
