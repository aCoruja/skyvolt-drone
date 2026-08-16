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

##  Stack Tecnológica (Desktop App)

A interface gráfica foi estruturada com:

*   **Python **: Linguagem de desenvolvimento principal.
*   **PyQt5**: Toolkit para desenvolvimento da interface gráfica nativa.
*   **PyQtGraph**: Biblioteca de plotagem de alto desempenho integrada para renderização ágil de gráficos de telemetria em tempo real.

---

##  Como Rodar a Aplicação

### 1.
Certifique-se de que está no diretório raiz do projeto e execute:
```bash
pip install -r requirements.txt
python -m app.main
