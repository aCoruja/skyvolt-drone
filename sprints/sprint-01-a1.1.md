# Sprint 1 — A1/1 (entrega 17/08/2026)

Peso 2,0. Time de até 4 pessoas. Sem integração real com hardware nesta etapa — tudo com dado simulado. O que entra na nota é arquitetura, UI e governança de git, não o drone.

## Objetivos do trabalho (app desktop)

- [ ] Estruturar `app/` em MVC: `ui/` (telas do Qt Designer + .py compilado, zero lógica de negócio), `controllers/` (lógica de janelas, Signals & Slots), `models/` (estado/dados — histórico, setpoints), `main.py` só inicializando a aplicação.
- [ ] Montar o dashboard principal com layouts responsivos (grid/box, sem posição fixa/sobreposta) e hierarquia visual clara.
- [ ] Indicadores de tensão (V), corrente (I) e potência (P = V×I) em destaque (`QLCDNumber`/`QLabel`).
- [ ] Indicador de estado do disjuntor: verde "FECHADO/NORMAL" / vermelho "ABERTO/PROTEÇÃO ATIVADA".
- [ ] Gráfico de tendência (PyQtGraph ou Matplotlib) já carregado com histórico simulado ao abrir a tela — não pode abrir vazio.
- [ ] Botão "CORTE DE EMERGÊNCIA" com confirmação via `QMessageBox.question` antes de agir.
- [ ] `QDialog` modal de configuração de limites (mín. 2 regras — ex.: corrente e tensão), com `QSpinBox`/`QDoubleSpinBox` ou `QSlider`, devolvendo os valores pra tela principal.
- [ ] `QTableWidget` de histórico com colunas: Data/Hora, Tipo de Evento, Descrição, Valor Medido.
- [ ] Painel de configuração serial (`QComboBox` de porta COM, baud rate 9600/115200, timeout, botões Conectar/Desconectar) — só muda status visual nesta etapa, sem conexão real.
- [ ] Lógica de setpoint: ao ultrapassar o limite configurado, dashboard muda pra amarelo/vermelho e registra evento na tabela.
- [ ] Lógica de disjuntor: mudança de estado dispara `QMessageBox.warning` + linha nova na tabela.
- [ ] Cada integrante commita com o próprio usuário GitHub, distribuído ao longo do fim de semana (não tudo no domingo), com mensagens coerentes.
- [ ] Atualizar `README.md` da raiz com os nomes dos integrantes antes de entregar.

Detalhamento de cada requisito em [`docs/requisitos_app_desktop.md`](../docs/requisitos_app_desktop.md). Critérios de nota e pesos ficam registrados em [`avaliacoes/a1.1.md`](../avaliacoes/a1.1.md) — aqui é só a lista do que precisa ser feito.

## Objetivos do drone (trilha paralela, não vale nota nesta entrega)

Não bloqueia a A1/1 — avança só no tempo livre da equipe. Dimensionados pra caber de fato na janela desta sprint (14/08–17/08, ~4 dias, com o time ocupado no app), não pra fase inteira:

- [ ] Fechar a lista de compras do kit de prática (`sprint_equipe.md`, Prioridades 1-3) e fazer o pedido — prazo do AliExpress é 2-6 semanas, então só pedir cedo já garante que chegue a tempo da Fase 2 (25/08); é o único item da Fase 1 que precisa sair nesta janela específica.
- [ ] Conferir visualmente a suposição de furação do motor RS1606 (12×12mm/4×M2) em `hardware/frame/SkyVolt_Arm.stl` contra o datasheet oficial — validação de medida no papel, sem imprimir.
- [ ] **Não** iniciar montagem, solda ou impressão em lote nesta sprint — isso é Fase 2 (25/08–14/09) de `sprint_equipe.md`, fora do escopo desta entrega.

A Fase 1 completa (compra) só fecha em 24/08 — o objetivo aqui é iniciar o pedido a tempo, não terminar a fase até 17/08.

## Entrega

- Link do repositório no Google Forms até 17/08/2026
- Apresentação/demo em sala no mesmo dia, rodando o código clonado do GitHub (não o que está aberto na IDE de alguém) — testar um clone limpo antes de ir pra aula
