from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.database.connection import Database
from app.models.evento import Evento, criar_evento
from app.models.repositorios import TAG_DISJUNTOR, DispositivoRepository, EventoRepository


class FalhaSimuladaError(RuntimeError):
    """Interrupção provocada de propósito entre o UPDATE do disjuntor e o INSERT do
    histórico, usada na arguição técnica para demonstrar o ROLLBACK ao vivo."""


@dataclass
class ResultadoComando:
    sucesso: bool
    status_no_banco: str  # status do disjuntor lido do banco depois da operação
    evento: Evento | None = None
    erro: str = ""


class CorteEmergencialService:
    """Comando do disjuntor principal como transação atômica (tudo ou nada):
    1) UPDATE dispositivos (status do disjuntor)  2) INSERT historico_eventos.
    Se qualquer passo falhar, `with conn:` executa ROLLBACK e nenhum dos dois fica gravado.
    """

    @staticmethod
    def executar(
        novo_status: str,
        descricao: str,
        severidade: str,
        valor_medido: float | None = None,
        simular_falha: bool = False,
    ) -> ResultadoComando:
        conn = Database.get_connection()
        try:
            with conn:  # BEGIN ... COMMIT, ou ROLLBACK se houver exceção
                disjuntor = DispositivoRepository.obter_por_tag(TAG_DISJUNTOR, conn=conn)
                if disjuntor is None:
                    raise LookupError(f"Dispositivo {TAG_DISJUNTOR} não cadastrado.")

                # Passo 1: atualização do atuador
                DispositivoRepository.atualizar_status(TAG_DISJUNTOR, novo_status, conn=conn)

                # Interrupção forçada para a demonstração da arguição técnica
                if simular_falha:
                    raise FalhaSimuladaError(
                        "interrupção simulada entre a atualização do disjuntor e o registro no histórico"
                    )

                # Passo 2: registro do evento correspondente
                evento = criar_evento(
                    tipo="Disjuntor",
                    descricao=descricao,
                    severidade=severidade,
                    valor_medido=valor_medido,
                    dispositivo_id=disjuntor.id,
                )
                EventoRepository.inserir(evento, conn=conn)

            return ResultadoComando(sucesso=True, status_no_banco=novo_status, evento=evento)

        except (sqlite3.Error, FalhaSimuladaError, LookupError, ValueError) as erro:
            return ResultadoComando(
                sucesso=False,
                status_no_banco=DispositivoRepository.obter_status(TAG_DISJUNTOR),
                erro=str(erro),
            )
        finally:
            conn.close()
