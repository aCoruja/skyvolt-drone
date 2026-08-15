# Sprint 1 — A1/1 (entrega 17/08/2026)

Peso 2,0. Time de até 4 pessoas. Sem integração real com hardware nesta etapa — tudo com dado simulado. O que entra na nota é arquitetura, UI e governança de git, não o drone.

## Objetivos do trabalho (app desktop) — entrega 17/08/2026

Escopo fechado: só o que o app desktop precisa ter pra essa entrega. Cada item abaixo cobre tanto o requisito obrigatório do professor (`docs/requisitos_app_desktop.md`) quanto o que o SkyVolt precisa de fato pra fazer sentido como estação de controle do drone (dado simulado como se viesse do ESP32 #2 via LoRa — sem conexão real ainda).

- [ ] Estruturar `app/` em MVC: `ui/` (telas do Qt Designer + .py compilado, zero lógica de negócio), `controllers/` (lógica de janelas, Signals & Slots), `models/` (estado/dados — telemetria, histórico, setpoints), `main.py` só inicializando a aplicação.
- [ ] Montar o dashboard principal com layouts responsivos (grid/box, sem posição fixa/sobreposta) e hierarquia visual clara.
- [ ] Indicadores de tensão (V), corrente (I) e potência (P = V×I) em destaque (`QLCDNumber`/`QLabel`) — exigência do professor.
- [ ] Indicador de temperatura e de classificação automática do circuito (AC/DC, faixa de tensão) — exigência própria do SkyVolt (`app/README.md`), sem a qual o dashboard não representa o que o drone realmente mede.
- [ ] Indicador de estado do disjuntor: verde "FECHADO/NORMAL" / vermelho "ABERTO/PROTEÇÃO ATIVADA" — disjuntor/proteção do circuito monitorado pelo drone, não do drone em si.
- [ ] Gráfico de tendência (PyQtGraph ou Matplotlib) já carregado com histórico simulado ao abrir a tela — não pode abrir vazio.
- [ ] Botão "CORTE DE EMERGÊNCIA" com confirmação via `QMessageBox.question` antes de agir.
- [ ] `QDialog` modal de configuração de limites (mín. 2 regras — ex.: corrente e tensão), com `QSpinBox`/`QDoubleSpinBox` ou `QSlider`, devolvendo os valores pra tela principal.
- [ ] `QTableWidget` de histórico com colunas: Data/Hora, Tipo de Evento, Descrição, Valor Medido.
- [ ] Painel de configuração de recepção (`QComboBox` de porta COM, baud rate 9600/115200, timeout, botões Conectar/Desconectar) — representa a futura recepção LoRa do ESP32 #2; só muda status visual nesta etapa, sem conexão real.
- [ ] Lógica de setpoint: ao ultrapassar o limite configurado, dashboard muda pra amarelo/vermelho e registra evento na tabela.
- [ ] Lógica de disjuntor: mudança de estado dispara `QMessageBox.warning` + linha nova na tabela.
- [ ] Cada integrante commita com o próprio usuário GitHub, distribuído ao longo do fim de semana (não tudo no domingo), com mensagens coerentes.
- [ ] Atualizar `README.md` da raiz com os nomes dos integrantes antes de entregar.

Detalhamento de cada requisito em [`docs/requisitos_app_desktop.md`](../docs/requisitos_app_desktop.md). Critérios de nota e pesos ficam registrados em [`avaliacoes/a1.1.md`](../avaliacoes/a1.1.md) — aqui é só a lista do que precisa ser feito.

A Fase 1 completa (compra) só fecha em 24/08 — o objetivo aqui é iniciar o pedido a tempo, não terminar a fase até 17/08.

## Entrega

- Link do repositório no Google Forms até 17/08/2026
- Apresentação/demo em sala no mesmo dia, rodando o código clonado do GitHub (não o que está aberto na IDE de alguém) — testar um clone limpo antes de ir pra aula
