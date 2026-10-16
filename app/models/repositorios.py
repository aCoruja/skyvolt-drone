from __future__ import annotations

import sqlite3
from typing import Optional

from app.database.connection import Database
from app.models.configuracao import ConfiguracaoSistema
from app.models.evento import Evento


class DispositivoRepository:
    """CRUD para Atuadores / Disjuntor com SQL 100% parametrizado."""

    @staticmethod
    def obter_status(tag: str) -> str:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM dispositivos WHERE tag = ?;", (tag,))
        row = cursor.fetchone()
        conn.close()
        return row["status"] if row else "ABERTO"

    @staticmethod
    def atualizar_status(
        tag: str, status: str, conn: Optional[sqlite3.Connection] = None
    ) -> None:
        fechar = False
        if conn is None:
            conn = Database.get_connection()
            fechar = True

        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE dispositivos
            SET status = ?, ultima_atualizacao = datetime('now', 'localtime')
            WHERE tag = ?;
            """,
            (status, tag),
        )

        if fechar:
            conn.commit()
            conn.close()


class EventoRepository:
    """CRUD para Histórico permanente de Eventos."""

    @staticmethod
    def inserir(evento: Evento, conn: Optional[sqlite3.Connection] = None) -> int:
        fechar = False
        if conn is None:
            conn = Database.get_connection()
            fechar = True

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico_eventos (data_hora, tipo_evento, valor_medido, descricao, severidade)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                evento.data_hora,
                evento.tipo_evento,
                evento.valor_medido,
                evento.descricao,
                evento.severidade,
            ),
        )
        novo_id = cursor.lastrowid or 0

        if fechar:
            conn.commit()
            conn.close()
        return novo_id

    @staticmethod
    def listar_todos(limite: int = 200) -> list[Evento]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, data_hora, tipo_evento, valor_medido, descricao, severidade
            FROM historico_eventos
            ORDER BY id DESC
            LIMIT ?;
            """,
            (limite,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Evento(
                id=row["id"],
                data_hora=row["data_hora"],
                tipo_evento=row["tipo_evento"],
                valor_medido=row["valor_medido"],
                descricao=row["descricao"],
                severidade=row["severidade"],
            )
            for row in rows
        ]


class RegrasLimitesRepository:
    """CRUD de limites operacionais cadastrados via modal."""

    @staticmethod
    def carregar() -> Optional[ConfiguracaoSistema]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM regras_limites WHERE id = 1;")
        row = cursor.fetchone()
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
        conn = Database.get_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO regras_limites (
                    id, tensao_min_ac, tensao_max_ac, tensao_min_dc, tensao_max_dc,
                    corrente_max, disjuntor_automatico, tempo_reacao_s, intervalo_leitura_s, periodo_historico
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
            )
        conn.close()
