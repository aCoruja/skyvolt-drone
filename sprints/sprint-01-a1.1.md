# Sprint 1 — A1/1 (entrega 17/08/2026)

Peso 2,0. Time de até 4 pessoas. Sem integração real com hardware nesta etapa — tudo com dado simulado. O que entra na nota é arquitetura, UI e governança de git, não o drone.

## Estrutura obrigatória (dentro de `app/`)

```
app/
  ui/            .ui do Qt Designer + telas compiladas .py — zero lógica de negócio aqui
  controllers/   classes de controle, lógica de janelas, Signals & Slots
  models/        (implícito no critério de MVC — dados/estado, ex. histórico, setpoints)
  main.py        só inicializa a aplicação, enxuto
```

## Checklist por critério de nota

### 1. Arquitetura & MVC — 2,5 pts
- [ ] Pastas `ui/`, `controllers/`, `models/` separadas, sem lógica de negócio dentro de `ui/`
- [ ] `main.py` só instancia e chama a janela principal
- [ ] Classes com responsabilidade única, nomes claros, sem gambiarra

### 2. UI/UX & layouts responsivos — 2,0 pts
- [ ] Tudo no Qt Designer usa Layouts (grid/box), nada com posição fixa/sobreposta
- [ ] Hierarquia visual clara (títulos, campos, botões bem separados)
- [ ] Paleta/fontes consistentes entre as janelas
- [ ] Navegação entre janela principal ↔ diálogo de config funciona sem travar

### 3. Telemetria & gráfico pré-carregado — 2,0 pts
- [ ] Indicadores V (tensão), I (corrente), P (potência, calculada como V×I) — QLCDNumber ou QLabel destacado
- [ ] Indicador de disjuntor: verde "FECHADO / NORMAL" / vermelho "ABERTO / PROTEÇÃO ATIVADA"
- [ ] Gráfico de tendência (PyQtGraph ou Matplotlib) **já carregado com histórico simulado** ao abrir a tela (não pode abrir vazio)

### 4. Componentes avançados & múltiplas janelas — 2,0 pts
- [ ] Botão "CORTE DE EMERGÊNCIA" com `QMessageBox.question` de confirmação antes de agir
- [ ] `QDialog` modal de configuração de limites, com **no mínimo 2 regras** (ex.: limite de corrente, limite de tensão), enviando os valores de volta pra tela principal
- [ ] `QSpinBox`/`QDoubleSpinBox` ou `QSlider` pro ajuste de limite de consumo
- [ ] `QTableWidget` de histórico com as colunas: Data/Hora, Tipo de Evento, Descrição, Valor Medido
- [ ] Painel de config. serial: `QComboBox` de porta COM, baud rate (9600/115200), timeout, botões Conectar/Desconectar (só muda status visual nesta etapa, não conecta de verdade)
- [ ] Ao ultrapassar o setpoint configurado: dashboard muda pra amarelo/vermelho + registra evento na tabela
- [ ] Mudança de estado do disjuntor dispara `QMessageBox.warning` + linha nova na tabela

### 5. Governança & Git — 1,5 pt
- [ ] Cada integrante commita com o **próprio usuário GitHub** (não só uma pessoa)
- [ ] Commits distribuídos ao longo do fim de semana, não tudo de uma vez no domingo
- [ ] Mensagens de commit coerentes (o que mudou, não "fix", "wip", "asd")
- [ ] README do projeto (raiz do repo) identifica a equipe e o projeto — **atualizar `README.md` com os nomes dos integrantes antes de entregar**

## Entrega

- Link do repositório no Google Forms até 17/08/2026
- Apresentação/demo em sala no mesmo dia, rodando o código clonado do GitHub (não o que está aberto na IDE de alguém) — testar um clone limpo antes de ir pra aula
