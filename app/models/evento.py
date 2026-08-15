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


def criar_evento(tipo: str, descricao: str, severidade: str) -> Evento:
    """Cria um Evento com data/hora atuais — usado pelo controller para
    registrar eventos em tempo real (ex.: acionamento do disjuntor).

    TODO(Vitoria): preencher data/hora (ex.: datetime.now() formatado como em
    eventos_iniciais()) e retornar o Evento.
    """
    raise NotImplementedError


def evento_para_linha(evento: Evento) -> list[str]:
    """Converte um Evento na lista de strings, na mesma ordem de COLUNAS,
    para popular uma linha do QTableWidget.

    TODO(Vitoria): retornar [evento.data, evento.hora, evento.tipo,
    evento.descricao, evento.severidade].
    """
    raise NotImplementedError
