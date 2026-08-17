# Sprint 1 — Divisão de Tarefas (A1/1)

**Entrega:** 17/08/2026 · **Documento criado:** 16/08/2026 · **Referência:** [`ideia_A1_1.md`](ideia_A1_1.md) (checklist oficial da entrega) e [`roadmap.md`](roadmap.md) (Sprint 1)

Este documento detalha **quem faz o quê** no que falta para a A1/1, com base no padrão de trabalho que o time já vinha seguindo (cada pessoa concentrada numa camada da arquitetura MVC).

---

## 1. Estado atual (levantamento de 16/08/2026)

O app já **roda sem erros** (`python -m app.main`) e a estrutura MVC está correta (`ui/` sem lógica, `controllers/` com os signals/slots, `models/` com os dados). O que falta para bater o checklist da entrega:

| Item do checklist | Situação | Bloqueia |
|---|---|---|
| Gráfico de tendência já populado ao abrir (não pode abrir vazio) | ❌ `graficoConsumo` só recebe eixo/grid, nunca dado (`main_controller.py:67`) | — (Matheus resolve sozinho) |
| Indicador de Temperatura | ❌ não existe na UI nem no model | Robertson (UI) + Vitória (model) |
| Classificação automática do circuito (AC/DC, faixa de tensão) | ❌ não existe na UI nem no model | Robertson (UI) + Vitória (model) |
| Painel de Recepção (simulado): combo porta COM, baud rate 9600/115200, timeout, Conectar/Desconectar | ❌ não existe | Robertson (UI) |
| Corte de emergência com `QMessageBox.question` de confirmação | ❌ `alternar_disjuntor()` age direto, sem confirmar | — (Matheus resolve sozinho) |
| Formatação PT-BR nos valores (vírgula decimal) | ⚠️ `formatacao.py` já existe mas não é usado — labels mostram `str(valor)` cru | — (Matheus resolve sozinho) |
| `dateInicio` do `ConfigDialog` não é preenchido a partir da configuração atual | ⚠️ TODO em `config_controller.py:32` | — (Matheus resolve sozinho) |

---

## 2. Robertson Moura ([@Sophthe141](https://github.com/Sophthe141)) — UI / Qt Designer

Área de sempre: `app/ui/*.ui` + `.qss`. **Não mexer em lógica** (nenhum `.py` de `controllers/` ou `models/`) — só desenhar os widgets e deixar os `objectName` certos para o controller.

### Tarefas

1. **Indicador de Temperatura** — no `main_window.ui`, dentro do mesmo `verticalLayout` onde estão `lblTensaoValor`/`lblCorrenteValor`/`lblPotenciaValor`:
   - Um `QLabel` de legenda (padrão dos `txtCorrenteValor_x` que já existem, ex. "TEMPERATURA (°C):").
   - Um `QLabel` de valor com `objectName = lblTemperaturaValor` (mesmo padrão de `lblTensaoValor`).

2. **Classificação automática do circuito** — mesmo bloco:
   - `QLabel` de legenda ("CLASSIFICAÇÃO:").
   - `QLabel` de valor com `objectName = lblClassificacaoValor`.

3. **Painel de Recepção (simulado)** — novo `QGroupBox` (ex. "Recepção LoRa"), pode ficar abaixo dos botões `btnAlternarDisjuntor`/`btnConfiguracoes` ou num layout novo à direita:
   - `QComboBox objectName = cmbPortaCOM` (itens de exemplo: `COM1`, `COM2`, `COM3` — vai ser populado por código depois, mas deixe 2-3 itens fixos por enquanto).
   - `QComboBox objectName = cmbBaudRate` com itens `9600` e `115200`.
   - `QSpinBox objectName = spnTimeout` (ex. 1–30, padrão 5).
   - `QPushButton objectName = btnConectar` (texto "Conectar").
   - `QPushButton objectName = btnDesconectar` (texto "Desconectar", pode iniciar desabilitado).
   - `QLabel objectName = lblStatusConexao` (texto inicial "Desconectado").

4. **Regenerar o `_ui.py`** depois de editar o `.ui` no Qt Designer:
   ```bash
   pyuic5 app/ui/main_window.ui -o app/ui/main_window_ui.py
   ```
   Não editar `main_window_ui.py` na mão — ele é gerado (tem o aviso "WARNING: Any manual changes... will be lost").

5. Commitar **com seu próprio usuário GitHub** (`@Sophthe141`), em pelo menos 2 commits separados ao longo do dia (não tudo de uma vez) — é critério de nota do professor.

### Critério de pronto
Abrir `python -m app.main` e ver na tela: label de Temperatura, label de Classificação, e o grupo de Recepção com os widgets acima — mesmo que ainda sem lógica por trás (é o próximo passo, do Matheus).

---

## 3. Vitória ([@Viihvendausen](https://github.com/Viihvendausen)) — Models / Simulação de dados

Área de sempre: `app/models/telemetria.py`, `dados_simulados.py`, `evento.py`, `formatacao.py`. **Não mexer em `controllers/` nem em `ui/`.**

### Tarefas

1. **Estender `LeituraTelemetria`** em `telemetria.py` com os dois campos novos:
   ```python
   @dataclass
   class LeituraTelemetria:
       timestamp: datetime
       tensao: float
       corrente: float
       disjuntor_fechado: bool
       temperatura: float      # novo
       classificacao: str      # novo — ex. "AC 220V", "DC 12V"
   ```

2. **Simular temperatura** em `ler_telemetria()` — algo simples e plausível, ex. `random.gauss(35.0, 3.0)` (°C, ambiente de quadro elétrico), arredondado em 1 casa.

3. **Função de classificação automática** — nova função em `telemetria.py`:
   ```python
   def classificar_circuito(leitura: LeituraTelemetria) -> str:
       """Classifica o circuito como AC/DC e a faixa de tensão, a partir da leitura simulada."""
   ```
   Para a simulação (ainda sem hardware real — isso só entra na Unidade 4), pode fixar um critério simples e documentado no docstring, ex.: acima de 100V = "AC 220V", abaixo = "DC 12V" — o importante é que a função exista e retorne algo coerente com `leitura.tensao`, já que o professor só pede que o indicador **exista e funcione com dado simulado**.

4. **Atualizar `dados_simulados.py`** (`gerar_curva_consumo`) para também gerar uma lista de temperaturas (mesmo padrão de `horas`/`tensoes`/`correntes`), já que o gráfico populado (tarefa do Matheus) pode querer plotar temperatura também no futuro. Não é obrigatório para o gráfico inicial (que é de tensão), mas deixa pronto.

5. **Formatação** — conferir se `formatacao.py` precisa de um `formatar_temperatura(valor: float) -> str` (padrão `"xx,x °C"`, mesmo estilo de `formatar_tensao`). Adicionar se fizer sentido.

6. Commitar **com seu próprio usuário GitHub** (`@Viihvendausen`), em mais de um commit ao longo do dia.

### Critério de pronto
`ler_telemetria()` retorna `temperatura` e `classificacao` preenchidos; `classificar_circuito()` existe e tem pelo menos um teste manual (`python -c "..."`) mostrando que funciona para tensão alta e baixa.

---

## 4. Matheus ([@aCoruja](https://github.com/aCoruja)) — Controllers / Integração

Área de sempre: `app/controllers/*.py`. Consome o que Robertson (UI) e Vitória (models) entregarem. As tarefas abaixo **1 a 4 não dependem de ninguém** e podem começar imediatamente; **5 e 6 dependem** dos outros dois.

### Tarefas independentes (fazer primeiro)

1. **Ligar o gráfico** — em `main_controller.py`, importar `gerar_curva_consumo` de `app.models.dados_simulados` e, em `carregar_grafico()`, plotar o histórico simulado assim que a janela abre (`self.graficoConsumo.plot(horas, tensoes, ...)`), para não abrir vazio.

2. **Usar `formatacao.py`** em `atualizar_telemetria()` no lugar de `str(leitura.tensao)` etc. — trocar pelos `formatar_tensao`/`formatar_corrente`/`formatar_potencia` já prontos.

3. **Confirmação no corte de emergência** — em `alternar_disjuntor()`, antes de abrir o disjuntor, chamar `QMessageBox.question(...)` e só agir se o usuário confirmar (só precisa confirmar ao **abrir**, não ao fechar).

4. **Corrigir `dateInicio`** — em `config_controller.py`, `preencher_dialog()`, preencher `self.dateInicio` a partir de `configuracao.data_inicio` (`QDate` a partir de `date` do Python — `QDate(ano, mes, dia)` ou `QDate.fromString`).

### Tarefas dependentes (fazer depois que Robertson/Vitória commitarem)

5. **Ligar Temperatura e Classificação** — em `atualizar_telemetria()`, atualizar `self.lblTemperaturaValor` e `self.lblClassificacaoValor` com os novos campos de `LeituraTelemetria` (depende dos objectName do Robertson e dos campos da Vitória).

6. **Ligar o painel de Recepção** — conectar `btnConectar`/`btnDesconectar` para só alternar `lblStatusConexao` visualmente (o requisito da A1/1 é só simulado — não precisa abrir porta serial de verdade ainda, isso é Unidade 4).

### Critério de pronto
Checklist completo de [`ideia_A1_1.md`](ideia_A1_1.md) batendo, app rodando sem erro, gráfico populado ao abrir.

---

## 5. Ordem de dependências

```
Robertson (UI: labels + painel LoRa)  ─┐
                                        ├──► Matheus (tarefas 5-6: ligar na lógica)
Vitória (models: temperatura/classif.) ─┘

Matheus (tarefas 1-4): sem dependência, pode rodar em paralelo com os dois acima
```

Robertson e Vitória podem trabalhar ao mesmo tempo — não mexem nos mesmos arquivos. Matheus faz 1-4 enquanto espera, depois puxa os commits dos outros dois (`git pull`) e faz 5-6 por último.

---

## 6. Regras do professor (lembrete — valem para todos)

- **Cada integrante precisa aparecer no histórico de commits com o próprio usuário GitHub** — quem não commitar tira ZERO na entrega, independente do time ter entregue certo.
- **Não concentrar tudo nos commits de um único dia** — espalhar ao longo da sprint, mesmo que a maior parte do trabalho tenha sido feita perto do prazo.
- Mensagens de commit claras e coerentes com o que foi feito (ex. `feat(ui): adiciona indicadores de temperatura e classificação`, não `update`).

---

## 7. Checklist final antes de entregar

- [ ] Gráfico abre já populado (não vazio)
- [ ] Temperatura e Classificação AC/DC visíveis e atualizando
- [ ] Painel de Recepção (COM/baud/timeout/Conectar/Desconectar) presente, mesmo que só visual
- [ ] Corte de emergência pede confirmação (`QMessageBox.question`)
- [ ] Valores exibidos em formato PT-BR (vírgula decimal)
- [ ] `README.md` da raiz com os 3 integrantes e usuários GitHub corretos
- [ ] Commits dos 3 integrantes presentes, espalhados ao longo da sprint
