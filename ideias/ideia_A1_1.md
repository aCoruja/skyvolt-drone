# Objetivos do Trabalho - App Desktop SkyVolt (Entrega 17/08/2026)

> ⚠️ **AVISO IMPORTANTE:**
> Todo sprint descrito neste documento representa uma *ideia* e um planejamento de como poderá ser a entrega **A1-1**, e não significa que o resultado final será total e estritamente assim. O escopo pode sofrer adaptações. Para conferir o resultado final validado, consulte sempre o diretório `avaliações/`.

---

## 1. Arquitetura e Estrutura do Software
* **Implementar o Padrão MVC:** Organizar o projeto estritamente em pastas:
  * `ui/`: Apenas arquivos de interface (telas do Qt Designer e seus arquivos `.py` compilados). **Zero lógica de negócio.**
  * `controllers/`: Gerenciamento das janelas, *Signals* e *Slots*.
  * `models/`: Gerenciamento de estado e dados (histórico simulado, telemetria, valores de setpoints).
  * `main.py`: Arquivo de entrada exclusivo para inicializar a aplicação.

## 2. Interface Gráfica (UI) e Layout
* **Dashboard Responsivo:** Construir o painel principal utilizando *layouts* adequados (Grid/Box), garantindo hierarquia visual sem usar posições fixas ou sobrepostas.
* **Indicadores Obrigatórios (Professor):** Exibir com destaque a Tensão (V), Corrente (I) e Potência (P) usando `QLCDNumber` ou `QLabel`.
* **Indicadores Específicos do SkyVolt:** Mostrar a Temperatura e a Classificação Automática do Circuito (AC/DC e faixa de tensão).
* **Status do Disjuntor (Circuito Monitorado):** Adicionar indicador visual do disjuntor do circuito inspecionado pelo drone (Verde para "FECHADO/NORMAL" e Vermelho para "ABERTO/PROTEÇÃO ATIVADA").
* **Gráfico de Tendência Inicializado:** Integrar um gráfico (via PyQtGraph ou Matplotlib) que já inicie populado com um histórico simulado de dados ao abrir o aplicativo (não pode abrir vazio).
* **Painel de Recepção (Simulado):** Criar a área de configuração da comunicação (futuro rádio LoRa) com `QComboBox` para porta COM, opções de *baud rate* (9600/115200), *timeout* e botões de Conectar/Desconectar. Nesta etapa, deve apenas alterar o status visualmente.

## 3. Funcionalidades e Interações (Lógica e *Widgets*)
* **Botão de Corte de Emergência:** Implementar a ação de corte exigindo uma janela de confirmação de segurança (`QMessageBox.question`) antes de prosseguir.
* **Configuração de Limites (Setpoints):** Criar uma janela modal (`QDialog`) para definir regras de limite de operação (mínimo de 2 regras, ex.: Tensão e Corrente). Utilizar `QSpinBox`, `QDoubleSpinBox` ou `QSlider`. Os valores devem ser devolvidos e aplicados na tela principal.
* **Tabela de Histórico de Eventos:** Implementar um `QTableWidget` contendo as colunas: Data/Hora, Tipo de Evento, Descrição e Valor Medido.

## 4. Lógica de Negócio (Eventos e Simulação)
* **Gatilho de Setpoint:** Criar a lógica para que, quando um dado simulado ultrapassar o limite configurado, o dashboard mude para estado de alerta (cores amarelo/vermelho) e uma nova linha seja registrada automaticamente na Tabela de Histórico.
* **Gatilho de Disjuntor:** Fazer com que a mudança simulada de estado do disjuntor dispare um aviso na tela (`QMessageBox.warning`) e adicione um novo registro na Tabela de Histórico.

## 5. Controle de Versão e Entregáveis (Regras da Equipe)
* **Commits Individuais:** Cada membro deve *commitar* o código usando seu próprio usuário do GitHub.
* **Distribuição de Trabalho:** Os *commits* devem ser distribuídos ao longo do final de semana de forma realista (não concentrar tudo no domingo). As mensagens de *commit* devem ser claras e coerentes com a funcionalidade entregue.
* **Documentação Final:** O arquivo `README.md` da raiz do repositório deve ser atualizado com os nomes de todos os integrantes antes do fechamento da entrega.
