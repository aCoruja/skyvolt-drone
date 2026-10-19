# A1/1 — App desktop PyQt com dados simulados

**Entrega:** 17/08/2026 · **Peso:** 2,0 · **Status:** Feito

Primeira entrega da disciplina: aplicativo desktop em PyQt5 com arquitetura MVC, dashboard com dados simulados em memória, janela modal de limites e tabela de histórico de eventos. O planejamento está em [`ideias/ideia_A1_1.md`](../../ideias/ideia_A1_1.md) (checklist) e [`ideias/sprint-01-a1.1.md`](../../ideias/sprint-01-a1.1.md) (divisão de tarefas).

Versão entregue: commit [`0e13dfa`](https://github.com/aCoruja/skyvolt-drone/tree/0e13dfa) (17/08/2026).

## Nota e devolutiva do professor

| Nota | Feedback | Pontos a corrigir |
|---|---|---|
| _a preencher_ | _a preencher_ | _a preencher_ |

## O que foi entregue

| Item do checklist | Situação | Onde |
|---|---|---|
| Arquitetura MVC (`ui/`, `controllers/`, `models/`, `main.py`) | ✅ | `app/` |
| Dashboard com layouts (sem posições fixas) | ✅ | `app/ui/main_window.ui` |
| Tensão, Corrente e Potência em destaque | ✅ | `lblTensaoValor`, `lblCorrenteValor`, `lblPotenciaValor` |
| Classificação automática do circuito (AC/DC) | ✅ | `classificar_circuito()` em `app/models/telemetria.py` |
| Indicador de Temperatura | ❌ não entrou | — |
| Status do disjuntor (verde fechado / vermelho aberto) | ✅ | `lblStatusDisjuntor` + `app/models/formatacao.py` |
| Gráfico de tendência já populado ao abrir | ✅ | `gerar_curva_consumo()` + PyQtGraph |
| Painel de comunicação simulado (porta COM, baud 9600/115200, timeout, Conectar/Desconectar) | ✅ | `cmbPortaCOM`, `cmbBaudRate`, `spnTimeout`, `btnConectar`/`btnDesconectar` |
| Corte de emergência com confirmação (`QMessageBox.question`) | ✅ | `alternar_disjuntor()` em `app/controllers/main_controller.py` |
| Janela modal de limites (`QDialog`, mín. 2 regras) | ✅ | `app/controllers/config_controller.py` (tensão AC/DC, corrente, corte automático) |
| Tabela de histórico de eventos (`QTableWidget`) | ⚠️ parcial | colunas Data, Hora, Tipo, Descrição, Severidade; sem **Valor Medido** (incluída na A1/3) |
| Gatilho de setpoint (alerta + nova linha na tabela) | ✅ | `_avaliar_risco()` |
| Gatilho do disjuntor (`QMessageBox.warning` + registro) | ✅ | `_acionar_disjuntor_automatico()` |
| Valores em formato PT-BR (vírgula decimal) | ✅ | `app/models/formatacao.py` |
| README com os integrantes | ✅ | `README.md` (seção Equipe) |
| Commits dos 3 integrantes | ✅ | Matheus (@aCoruja), Vitória (@Viihvendausen), Sophia (@Sophthe141) |
