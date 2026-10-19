from __future__ import annotations

import os
import sqlite3
from datetime import datetime

# Raiz do aplicativo (pasta app/): data/ e logs/ ficam ao lado de database/, models/, etc.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "smartgrid.db")

TIMEOUT_S = 10.0  # espera por um lock antes de falhar com "database is locked"

TABELAS_ESPERADAS = ("dispositivos", "historico_eventos", "regras_limites")


class Database:
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        """Retorna uma conexão ativa com o SQLite configurada com:
        - timeout=10.0 (prevenção contra bloqueios de concorrência);
        - row_factory=sqlite3.Row (acesso seguro por nome de coluna);
        - PRAGMA foreign_keys = ON (ativação obrigatória de chaves estrangeiras).
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=TIMEOUT_S)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def init_db() -> None:
        """Inicializa automaticamente o banco smartgrid.db, criando o esquema
        relacional com todas as constraints explícitas (PRIMARY KEY, NOT NULL, CHECK,
        FOREIGN KEY), e valida o esquema ao final."""
        conn = Database.get_connection()
        try:
            # WAL: leituras não bloqueiam a escrita do corte emergencial (gera *.db-wal)
            conn.execute("PRAGMA journal_mode = WAL;")

            with conn:
                cursor = conn.cursor()

                # 1. Tabela de Dispositivos / Atuadores com CHECK de status
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dispositivos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag TEXT NOT NULL UNIQUE,
                        tipo TEXT NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('ABERTO', 'FECHADO')),
                        ultima_atualizacao TEXT NOT NULL
                    );
                    """
                )

                # 2. Histórico permanente de eventos da QTableWidget. Eventos de
                # atuador referenciam o dispositivo afetado (chave estrangeira).
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS historico_eventos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_hora TEXT NOT NULL,
                        tipo_evento TEXT NOT NULL,
                        valor_medido REAL,
                        descricao TEXT NOT NULL,
                        severidade TEXT NOT NULL CHECK(severidade IN ('Info', 'Alerta', 'Critico')),
                        dispositivo_id INTEGER,
                        FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)
                            ON UPDATE CASCADE ON DELETE RESTRICT
                    );
                    """
                )

                # 3. Regras / limites operacionais (linha única, id = 1)
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS regras_limites (
                        id INTEGER PRIMARY KEY CHECK(id = 1),
                        tensao_min_ac REAL NOT NULL CHECK(tensao_min_ac >= 0),
                        tensao_max_ac REAL NOT NULL CHECK(tensao_max_ac > tensao_min_ac),
                        tensao_min_dc REAL NOT NULL CHECK(tensao_min_dc >= 0),
                        tensao_max_dc REAL NOT NULL CHECK(tensao_max_dc > tensao_min_dc),
                        corrente_max REAL NOT NULL CHECK(corrente_max > 0),
                        disjuntor_automatico INTEGER NOT NULL CHECK(disjuntor_automatico IN (0, 1)),
                        tempo_reacao_s INTEGER NOT NULL CHECK(tempo_reacao_s > 0),
                        intervalo_leitura_s INTEGER NOT NULL CHECK(intervalo_leitura_s > 0),
                        periodo_historico TEXT NOT NULL
                    );
                    """
                )

                # Sementes idempotentes: Disjuntor Principal e Relé de Emergência
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for tag, tipo in (
                    ("DISJ_PRINCIPAL", "Disjuntor"),
                    ("RELE_EMERG", "Relé de Emergência"),
                ):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO dispositivos (tag, tipo, status, ultima_atualizacao)
                        VALUES (?, ?, 'FECHADO', ?);
                        """,
                        (tag, tipo, agora),
                    )

            Database._validar_esquema(conn)
        finally:
            conn.close()

    @staticmethod
    def _validar_esquema(conn: sqlite3.Connection) -> None:
        """Confere se as tabelas existem, se as chaves estrangeiras estão ativas e
        se não há registros órfãos. Lança sqlite3.DatabaseError se algo falhar."""
        encontradas = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?);",
                TABELAS_ESPERADAS,
            )
        }
        faltando = set(TABELAS_ESPERADAS) - encontradas
        if faltando:
            raise sqlite3.DatabaseError(f"Tabelas ausentes no esquema: {sorted(faltando)}")

        if conn.execute("PRAGMA foreign_keys;").fetchone()[0] != 1:
            raise sqlite3.DatabaseError("PRAGMA foreign_keys não está ativo.")

        if conn.execute("PRAGMA foreign_key_check;").fetchall():
            raise sqlite3.DatabaseError("Há registros violando chaves estrangeiras.")
