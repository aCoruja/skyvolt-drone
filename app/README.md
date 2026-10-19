#  SKYVOLT - Estação de Controle e Monitoramento Desktop

O **SKYVOLT** é um aplicativo desktop desenvolvido como entregável central da disciplina. Ele funciona como uma estação de controle e monitoramento, projetada para receber telemetria em tempo real via comunicação de rádio **LoRa** e apresentar dados críticos em um painel interativo.

---

##  Descrição do Projeto

O sistema é responsável por capturar, processar e apresentar as seguintes grandezas elétricas e físicas:
*   **Tensão** (V)
*   **Corrente** (A)
*   **Temperatura** (°C)
*   **Classificação do estado da rede** (Normal, Sobrecarga, Subtensão, etc.)
---

##  Requisitos e Funcionalidades

O escopo completo do projeto está distribuído nos seguintes documentos internos do repositório:

*   **Requisitos Funcionais Detalhados:** Encontre a lista completa (detalhando o Dashboard, controle do disjuntor, corte de emergência, definição de setpoints e tabela de histórico) em [requisitos_app_desktop.md](file:///docs/requisitos_app_desktop.md).
*   **Checklist da Primeira Entrega (Simulação):** O progresso e os itens avaliativos obrigatórios estão listados em [ideia_A1_1.md](file:///ideias/ideia_A1_1.md).
*   **Pendências e Definições Futuras:** A stack complementar (como banco de dados local definitivo e layout final do dashboard) ainda está em fase de definição — consulte a **Seção 8 (Pendências)** do documento conceitual [SkyVolt_Documento.pdf](file:///docs/SkyVolt_Documento.pdf).

---

## (Desktop App)

A interface gráfica foi estruturada com:

*   **Python **: Linguagem de desenvolvimento principal.
*   **PyQt5**: Toolkit para desenvolvimento da interface gráfica nativa.
*   **PyQtGraph**: Biblioteca de plotagem de alto desempenho integrada para renderização ágil de gráficos de telemetria em tempo real.

---

##  Como Rodar a Aplicação

Na raiz do repositório:

```bash
pip install -r requirements.txt
python -m app.main
```

Na primeira execução o app cria sozinho `app/data/smartgrid.db`, `app/data/config.json` e `app/logs/smartgrid.log`. Esses três arquivos não vão para o Git (ver `.gitignore`).

---

##  Entrega A1/3 — Persistência, JSON e Logs

### Estrutura

```
app/
├── database/     connection.py — conexão (timeout=10s), PRAGMA foreign_keys, WAL, Database.init_db()
├── models/       entidades, repositórios (SQL só com "?"), corte_emergencial.py, configuracao.py (config.json), logger_service.py
├── controllers/  janelas, sinais/slots e validação (main_controller.py, config_controller.py)
├── ui/           telas do Qt Designer (.ui -> .py), sem regra de negócio nem SQL
├── logs/         smartgrid.log
├── data/         config.json, smartgrid.db
└── main.py       ponto de entrada
```

### Banco `smartgrid.db`

| Tabela | Conteúdo | Restrições |
|---|---|---|
| `dispositivos` | disjuntor principal (`DISJ_PRINCIPAL`) e relé de emergência (`RELE_EMERG`) | `PRIMARY KEY`, `NOT NULL`, `UNIQUE(tag)`, `CHECK(status IN ('ABERTO','FECHADO'))` |
| `historico_eventos` | tudo que aparece na tabela de eventos | `CHECK` de severidade, `FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)` |
| `regras_limites` | limites cadastrados na janela de Configurações | `CHECK` de faixa (mín. < máx., corrente > 0, etc.) |

O **Corte Emergencial** é uma transação única (`with conn:`): atualiza o disjuntor e grava o evento. Se qualquer passo falhar, o SQLite faz `ROLLBACK` e nenhum dos dois fica gravado (`app/models/corte_emergencial.py`).

### Roteiro da demonstração (arguição técnica)

Rode a partir do clone do GitHub. Deixe o `app/logs/smartgrid.log` aberto num editor ou num terminal com `tail -f app/logs/smartgrid.log`.

1. **Início:** o log mostra `[INFO] Conexão com SQLite estabelecida e esquema validado.` Na primeira vez, também `[WARNING] Arquivo data/config.json inexistente. Criando com valores default.`
2. **Falha de validação:** em ⚙ Configurações:
   - apague todo o texto da Corrente máxima → *campo vazio*;
   - digite um valor negativo na Tensão mínima AC → *não pode ser negativa*;
   - tente digitar letras: o campo numérico nem aceita a digitação (bloqueio preventivo). Digitar só `-` e confirmar → *não é um número*.
   
   Cada tentativa abre um `QMessageBox` e gera `[WARNING] Entrada inválida bloqueada ...`. Nada é gravado.
3. **Alarme:** salve a Corrente máxima em `3 A`. O log mostra `[WARNING] Limite de corrente violado: 4.87A (Limite configurado: 3.00A).` e a tabela ganha um evento *Risco*.
4. **Falha transacional com rollback:** clique em **Corte Emergencial** → **Simular falha (teste de rollback)**. Aparece "Transação revertida (ROLLBACK)", o disjuntor continua **Fechado**, nenhuma linha nova entra na tabela e o log mostra `[ERROR] Falha na operação de corte emergencial. Rollback executado: interrupção simulada ...`.
5. **Corte normal:** **Corte Emergencial** → **Corte Emergencial**. O disjuntor abre, o evento aparece na tabela e o log mostra `[WARNING] Corte de carga executado ... (COMMIT)`.
6. **Persistência:** feche e abra o app. A tabela, o estado do disjuntor e os limites voltam do banco.
7. **Auditoria:** abra o `smartgrid.log` e mostre as linhas dos passos acima.

Para conferir o banco direto:

```bash
sqlite3 app/data/smartgrid.db "SELECT tag, status, ultima_atualizacao FROM dispositivos;"
```
