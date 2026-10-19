from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

from app.database.connection import Database
from app.models.configuracao import ConfiguracaoSistema
from app.models.evento import Evento

STATUS_VALIDOS = ("ABERTO", "FECHADO")
TAG_DISJUNTOR = "DISJ_PRINCIPAL"


@dataclass
class Dispositivo:
    tag: str
    tipo: str
    status: str  # "ABERTO" | "FECHADO"
    ultima_atualizacao: str = ""
    id: Optional[int] = None


def _linha_para_dispositivo(row: sqlite3.Row) -> Dispositivo:
    return Dispositivo(
        id=row["id"],
        tag=row["tag"],
        tipo=row["tipo"],
        status=row["status"],
        ultima_atualizacao=row["ultima_atualizacao"],
    )


def _linha_para_evento(row: sqlite3.Row) -> Evento:
    return Evento(
        id=row["id"],
        data_hora=row["data_hora"],
        tipo_evento=row["tipo_evento"],
        valor_medido=row["valor_medido"],
        descricao=row["descricao"],
        severidade=row["severidade"],
        dispositivo_id=row["dispositivo_id"],
    )


class DispositivoRepository:
    """CRUD para Atuadores / Disjuntor com SQL 100% parametrizado.

    Os métodos de escrita aceitam uma conexão externa (`conn`) para participar de
    uma transação maior — ver CorteEmergencialService. Sem `conn`, abrem e
    confirmam a própria transação.
    """

    @staticmethod
    def inserir(dispositivo: Dispositivo, conn: Optional[sqlite3.Connection] = None) -> int:
        def _executar(c: sqlite3.Connection) -> int:
            cursor = c.execute(
                """
                INSERT INTO dispositivos (tag, tipo, status, ultima_atualizacao)
                VALUES (?, ?, ?, datetime('now', 'localtime'));
                """,
                (dispositivo.tag, dispositivo.tipo, dispositivo.status),
            )
            return cursor.lastrowid or 0

        return _na_transacao(conn, _executar)

    @staticmethod
    def listar_todos() -> list[Dispositivo]:
        conn = Database.get_connection()
        try:
            rows = conn.execute(
                "SELECT id, tag, tipo, status, ultima_atualizacao FROM dispositivos ORDER BY id;"
            ).fetchall()
        finally:
            conn.close()
        return [_linha_para_dispositivo(row) for row in rows]

    @staticmethod
    def obter_por_tag(tag: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dispositivo]:
        def _executar(c: sqlite3.Connection) -> Optional[Dispositivo]:
            row = c.execute(
                "SELECT id, tag, tipo, status, ultima_atualizacao FROM dispositivos WHERE tag = ?;",
                (tag,),
            ).fetchone()
            return _linha_para_dispositivo(row) if row else None

        if conn is not None:
            return _executar(conn)
        c = Database.get_connection()
        try:
            return _executar(c)
        finally:
            c.close()

    @staticmethod
    def obter_status(tag: str) -> str:
        dispositivo = DispositivoRepository.obter_por_tag(tag)
        if dispositivo is None:
            raise LookupError(f"Dispositivo {tag!r} não cadastrado no banco.")
        return dispositivo.status

    @staticmethod
    def atualizar_status(tag: str, status: str, conn: Optional[sqlite3.Connection] = None) -> None:
        if status not in STATUS_VALIDOS:
            raise ValueError(f"Status inválido para atuador: {status!r}")

        def _executar(c: sqlite3.Connection) -> None:
            cursor = c.execute(
                """
                UPDATE dispositivos
                SET status = ?, ultima_atualizacao = datetime('now', 'localtime')
                WHERE tag = ?;
                """,
                (status, tag),
            )
            if cursor.rowcount != 1:
                raise LookupError(f"Dispositivo {tag!r} não encontrado para atualização.")

        _na_transacao(conn, _executar)

    @staticmethod
    def excluir(tag: str) -> bool:
        """Remove o dispositivo. Falha com sqlite3.IntegrityError se houver eventos
        no histórico apontando para ele (FOREIGN KEY ... ON DELETE RESTRICT)."""
        return _na_transacao(
            None,
            lambda c: c.execute("DELETE FROM dispositivos WHERE tag = ?;", (tag,)).rowcount == 1,
        )


class EventoRepository:
    """CRUD para o Histórico permanente de Eventos."""

    @staticmethod
    def inserir(evento: Evento, conn: Optional[sqlite3.Connection] = None) -> int:
        def _executar(c: sqlite3.Connection) -> int:
            cursor = c.execute(
                """
                INSERT INTO historico_eventos
                    (data_hora, tipo_evento, valor_medido, descricao, severidade, dispositivo_id)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    evento.data_hora,
                    evento.tipo_evento,
                    evento.valor_medido,
                    evento.descricao,
                    evento.severidade,
                    evento.dispositivo_id,
                ),
            )
            return cursor.lastrowid or 0

        novo_id = _na_transacao(conn, _executar)
        evento.id = novo_id
        return novo_id

    @staticmethod
    def listar_todos(limite: int = 500) -> list[Evento]:
        """Eventos mais recentes primeiro (id decrescente)."""
        conn = Database.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, data_hora, tipo_evento, valor_medido, descricao, severidade, dispositivo_id
                FROM historico_eventos
                ORDER BY id DESC
                LIMIT ?;
                """,
                (limite,),
            ).fetchall()
        finally:
            conn.close()
        return [_linha_para_evento(row) for row in rows]

    @staticmethod
    def obter_por_id(evento_id: int) -> Optional[Evento]:
        conn = Database.get_connection()
        try:
            row = conn.execute(
                """
                SELECT id, data_hora, tipo_evento, valor_medido, descricao, severidade, dispositivo_id
                FROM historico_eventos WHERE id = ?;
                """,
                (evento_id,),
            ).fetchone()
        finally:
            conn.close()
        return _linha_para_evento(row) if row else None

    @staticmethod
    def atualizar_descricao(evento_id: int, descricao: str) -> bool:
        return _na_transacao(
            None,
            lambda c: c.execute(
                "UPDATE historico_eventos SET descricao = ? WHERE id = ?;",
                (descricao, evento_id),
            ).rowcount == 1,
        )

    @staticmethod
    def excluir(evento_id: int) -> bool:
        return _na_transacao(
            None,
            lambda c: c.execute(
                "DELETE FROM historico_eventos WHERE id = ?;", (evento_id,)
            ).rowcount == 1,
        )

    @staticmethod
    def contar() -> int:
        conn = Database.get_connection()
        try:
            return conn.execute("SELECT COUNT(*) FROM historico_eventos;").fetchone()[0]
        finally:
            conn.close()


class RegrasLimitesRepository:
    """CRUD dos limites operacionais cadastrados via janela modal (linha única id = 1)."""

    @staticmethod
    def carregar() -> Optional[ConfiguracaoSistema]:
        conn = Database.get_connection()
        try:
            row = conn.execute(
                """
                SELECT tensao_min_ac, tensao_max_ac, tensao_min_dc, tensao_max_dc, corrente_max,
                       disjuntor_automatico, tempo_reacao_s, intervalo_leitura_s, periodo_historico
                FROM regras_limites WHERE id = ?;
                """,
                (1,),
            ).fetchone()
        finally:
            conn.close()

        if not row:
            return None

        return ConfiguracaoSistema(
            tensao_minima_ac=row["tensao_min_ac"],
            tensao_maxima_ac=row["tensao_max_ac"],
            tensao_minima_dc=row["tensao_min_dc"],
            tensao_maxima_dc=row["tensao_max_dc"],
            corrente_maxima=row["corrente_max"],
            disjuntor_automatico=bool(row["disjuntor_automatico"]),
            tempo_reacao_s=row["tempo_reacao_s"],
            intervalo_leitura_s=row["intervalo_leitura_s"],
            periodo_historico=row["periodo_historico"],
        )

    @staticmethod
    def salvar(config: ConfiguracaoSistema) -> None:
        """Insere ou atualiza (upsert) a linha de limites."""
        _na_transacao(
            None,
            lambda c: c.execute(
                """
                INSERT INTO regras_limites (
                    id, tensao_min_ac, tensao_max_ac, tensao_min_dc, tensao_max_dc,
                    corrente_max, disjuntor_automatico, tempo_reacao_s, intervalo_leitura_s,
                    periodo_historico
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    tensao_min_ac = excluded.tensao_min_ac,
                    tensao_max_ac = excluded.tensao_max_ac,
                    tensao_min_dc = excluded.tensao_min_dc,
                    tensao_max_dc = excluded.tensao_max_dc,
                    corrente_max = excluded.corrente_max,
                    disjuntor_automatico = excluded.disjuntor_automatico,
                    tempo_reacao_s = excluded.tempo_reacao_s,
                    intervalo_leitura_s = excluded.intervalo_leitura_s,
                    periodo_historico = excluded.periodo_historico;
                """,
                (
                    config.tensao_minima_ac,
                    config.tensao_maxima_ac,
                    config.tensao_minima_dc,
                    config.tensao_maxima_dc,
                    config.corrente_maxima,
                    1 if config.disjuntor_automatico else 0,
                    config.tempo_reacao_s,
                    config.intervalo_leitura_s,
                    config.periodo_historico,
                ),
            ),
        )

    @staticmethod
    def excluir() -> bool:
        """Apaga os limites salvos; no próximo início o app volta aos do config.json."""
        return _na_transacao(
            None, lambda c: c.execute("DELETE FROM regras_limites WHERE id = ?;", (1,)).rowcount == 1
        )


def _na_transacao(conn: Optional[sqlite3.Connection], operacao):
    """Executa `operacao(conn)`. Com conexão externa, apenas executa (quem chamou controla
    o COMMIT/ROLLBACK). Sem ela, abre uma conexão própria e usa `with conn:`, que faz
    COMMIT no sucesso e ROLLBACK automático se a operação lançar exceção."""
    if conn is not None:
        return operacao(conn)
    proprio = Database.get_connection()
    try:
        with proprio:
            return operacao(proprio)
    finally:
        proprio.close()
