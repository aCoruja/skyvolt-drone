from __future__ import annotations

import os
import sqlite3
from datetime import datetime


def obter_diretorio_base() -> str:
    """Localiza a pasta raiz do projeto de forma robusta em qualquer sistema operacional."""
    dir_arquivo = os.path.dirname(os.path.abspath(__file__))
    dir_pai = os.path.dirname(dir_arquivo)
    if os.path.basename(dir_pai) == "app":
        return os.path.dirname(dir_pai)
    return dir_pai


BASE_DIR = obter_diretorio_base()
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "smartgrid.db")


class Database:
    @staticmethod
    def get_connection() -> sqlite3.Connection:
        """Retorna uma conexão ativa com o SQLite configurada com:
        - timeout=10.0 (previne bloqueios de concorrência);
        - row_factory=sqlite3.Row (acesso por nome de coluna);
        - PRAGMA foreign_keys = ON (ativação mandatória da integridade referencial).
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @staticmethod
    def init_db() -> None:
        """Inicializa o banco smartgrid.db criando o esquema relacional
        com restrições PRIMARY KEY, NOT NULL e restrições CHECK."""
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = Database.get_connection()

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

            # 2. Tabela de Histórico de Eventos permanente
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS historico_eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora TEXT NOT NULL,
                    tipo_evento TEXT NOT NULL,
                    valor_medido REAL,
                    descricao TEXT NOT NULL,
                    severidade TEXT NOT NULL CHECK(severidade IN ('Info', 'Alerta', 'Critico'))
                );
                """
            )

            # 3. Tabela de Regras / Limites operacionais com restrições CHECK
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

            # Sementes iniciais: Disjuntor Principal e Relé de Emergência
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT OR IGNORE INTO dispositivos (tag, tipo, status, ultima_atualizacao)
                VALUES ('DISJ_PRINCIPAL', 'Disjuntor', 'FECHADO', ?);
                """,
                (agora,),
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO dispositivos (tag, tipo, status, ultima_atualizacao)
                VALUES ('RELE_EMERG', 'Relé de Emergência', 'FECHADO', ?);
                """,
                (agora,),
            )

        conn.close()
