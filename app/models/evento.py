from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Lista contendo as colunas conforme ordenação solicitada
COLUNAS = ["Data", "Hora", "Tipo", "Descrição", "Severidade"]


@dataclass
class Evento:
    data: str
    hora: str
    tipo: str
    descricao: str
    severidade: str  # "Info" | "Alerta" | "Critico"


def eventos_iniciais() -> list[Evento]:
    """Retorna registros variados (partida do sistema, subtensão, sobretensão,
    corrente alta, comando de disjuntor, retorno ao normal)."""
    eventos: list[Evento] = []
    
    # 8 Registros variados de exemplo inicializando o sistema
    eventos.append(Evento(data="15/08/2026", hora="06:00:12", tipo="Sistema",
                           descricao="Partida do sistema", severidade="Info"))
    eventos.append(Evento(data="15/08/2026", hora="07:15:40", tipo="Tensão",
                           descricao="Subtensão detectada na rede", severidade="Alerta"))
    eventos.append(Evento(data="15/08/2026", hora="08:02:05", tipo="Tensão",
                           descricao="Retorno ao normal", severidade="Info"))
    eventos.append(Evento(data="15/08/2026", hora="12:30:51", tipo="Corrente",
                           descricao="Corrente alta detectada", severidade="Critico"))
    eventos.append(Evento(data="15/08/2026", hora="12:31:10", tipo="Disjuntor",
                           descricao="Comando de abertura do disjuntor", severidade="Critico"))
    eventos.append(Evento(data="15/08/2026", hora="13:00:00", tipo="Disjuntor",
                           descricao="Comando de fechamento do disjuntor", severidade="Info"))
    eventos.append(Evento(data="15/08/2026", hora="18:45:22", tipo="Tensão",
                           descricao="Sobretensão detectada na rede", severidade="Alerta"))
    eventos.append(Evento(data="15/08/2026", hora="19:10:37", tipo="Tensão",
                           descricao="Retorno ao normal", severidade="Info"))
    
    return eventos


def criar_evento(tipo: str, descricao: str, severidade: str) -> Evento:
    """Cria um Evento com data/hora atuais — usado pelo controller para
    registrar eventos em tempo real (ex.: acionamento do disjuntor)."""
    agora = datetime.now()
    data = agora.strftime("%d/%m/%Y")
    hora = agora.strftime("%H:%M:%S")
    return Evento(data=data, hora=hora, tipo=tipo, descricao=descricao, severidade=severidade)


def evento_para_linha(evento: Evento) -> list[str]:
    """Converte um Evento na lista de strings, na mesma ordem de COLUNAS,
    para popular uma linha do QTableWidget."""
    return [evento.data, evento.hora, evento.tipo, evento.descricao, evento.severidade]
