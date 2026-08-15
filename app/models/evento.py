from __future__ import annotations

from dataclasses import dataclass

# Stub — assinatura travada (Trello #11, responsável: Vitoria).
# Manter a dataclass Evento e a lista COLUNAS como estão.

COLUNAS = ["Data", "Hora", "Tipo", "Descrição", "Severidade"]


@dataclass
class Evento:
    data: str
    hora: str
    tipo: str
    descricao: str
    severidade: str  # "Info" | "Alerta" | "Critico"


def eventos_iniciais() -> list[Evento]:
    """TODO(Vitoria): preencher com ~8 registros variados (partida do sistema,
    subtensão, sobretensão, corrente alta, comando de disjuntor, retorno ao
    normal), usando os campos data/hora/tipo/descricao/severidade."""
    eventos: list[Evento] = []
    # TODO: eventos.append(Evento(data=..., hora=..., tipo=..., descricao=..., severidade=...))
    return eventos
