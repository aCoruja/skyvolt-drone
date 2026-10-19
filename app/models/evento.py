from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Cabeçalhos da QTableWidget mapeados com o esquema relacional (tabela historico_eventos)
COLUNAS = ["ID", "Data/Hora", "Tipo", "Valor Medido", "Descrição", "Severidade"]

SEVERIDADES = ("Info", "Alerta", "Critico")


@dataclass
class Evento:
    data_hora: str
    tipo_evento: str
    valor_medido: Optional[float]
    descricao: str
    severidade: str  # "Info" | "Alerta" | "Critico"
    dispositivo_id: Optional[int] = None
    id: Optional[int] = None


def criar_evento(
    tipo: str,
    descricao: str,
    severidade: str,
    valor_medido: Optional[float] = None,
    dispositivo_id: Optional[int] = None,
) -> Evento:
    """Cria uma nova entidade Evento com data e hora do momento da ocorrência."""
    if severidade not in SEVERIDADES:
        raise ValueError(f"Severidade inválida: {severidade!r}")
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Evento(
        data_hora=agora,
        tipo_evento=tipo,
        valor_medido=valor_medido,
        descricao=descricao,
        severidade=severidade,
        dispositivo_id=dispositivo_id,
    )


def evento_para_linha(evento: Evento) -> list[str]:
    """Converte a entidade Evento em uma lista ordenada para popular a QTableWidget."""
    id_str = str(evento.id) if evento.id is not None else "—"
    valor_str = f"{evento.valor_medido:.2f}" if evento.valor_medido is not None else "—"
    return [
        id_str,
        evento.data_hora,
        evento.tipo_evento,
        valor_str,
        evento.descricao,
        evento.severidade,
    ]
