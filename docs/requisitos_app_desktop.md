# Requisitos funcionais — Aplicativo desktop (HMI de supervisão energética)

> Especificação repassada pelo professor para a última entrega do semestre (Unidade 4 / apresentação final, 01–02/12/2026). Complementa `SkyVolt_Documento.pdf` (requisitos, arquitetura e BOM gerais do projeto) e detalha especificamente o comportamento esperado do software desktop. O checklist de nota da primeira entrega (simulada, sem hardware real) está em [`ideias/ideia_A1_1.md`](../ideias/ideia_A1_1.md); este documento descreve o alvo final, incluindo a integração serial real que entra a partir da Unidade 4.

## Visão geral

O software desktop atua como uma **Interface Homem-Máquina (IHM) de supervisão energética**, responsável por processar os sinais analógicos e digitais recebidos do microcontrolador e por permitir a intervenção do operador em tempo real.

## 1. Processamento e apresentação de telemetria (Hardware → Desktop)

O software recebe continuamente as amostras brutas dos sensores do microcontrolador (via comunicação serial, quando a integração real estiver pronta, ou simuladas nas entregas anteriores à Unidade 4).

- **Leitura e tratamento de tensão (V) e corrente (A):** ler a tensão eficaz (V<sub>RMS</sub>) e a corrente (I<sub>RMS</sub>) enviadas pelo sensor (ex.: ACS712 / ZMPT101B).
- **Cálculo da potência ativa (P):** calcular a potência instantânea aproximada em Watts (W) ou Quilowatts (kW):

  ```
  P = V × I
  ```

- **Renderização no dashboard:**
  - Exibir os valores instantâneos de V, I e P em indicadores numéricos de alta visibilidade (`QLCDNumber` ou `QLabel` customizadas com destaque de cor).
  - Atualizar o gráfico de tendência temporal (PyQtGraph ou Matplotlib) plotando a curva de consumo de potência ao longo do tempo. O gráfico deve ser inicializado **com histórico pré-carregado** no momento da abertura da tela (não pode abrir vazio).

## 2. Monitoramento de estado binário e segurança (Hardware → Desktop)

O software monitora o estado físico do disjuntor/chave de proteção geral da instalação.

- **Sinalização visual de estado (aberto / fechado):**
  - **Fechado** (energizado / normal): indicador verde — *"Disjuntor: FECHADO / NORMAL"*.
  - **Aberto** (desenergizado / trip/falha): indicador vermelho — *"Disjuntor: ABERTO / PROTEÇÃO ATIVADA"*.
- **Detecção e registro de eventos de disparo:** sempre que o estado mudar espontaneamente no hardware (ex.: disjuntor caiu por sobrecarga), o software dispara um aviso visual (`QMessageBox.warning`) e gera um registro automático na tabela de histórico.

## 3. Atuação e parametrização do sistema (Desktop → Hardware)

O software fornece ao operador meios de intervir na carga e de definir parâmetros operacionais.

- **Corte emergencial da carga (relé de saída):**
  - Botão de grande destaque ("CORTE DE EMERGÊNCIA" / "DESLIGAR CARGA").
  - Ao ser acionado, exibe caixa de confirmação modal (`QMessageBox.question`). Se confirmado, envia o comando binário (ex.: `RELAY_OFF`) para o microcontrolador abrir o relé.
- **Ajuste de limite de alerta de consumo (setpoints):** o operador define um limite máximo tolerável de corrente ou potência via campo numérico (`QSpinBox` / `QDoubleSpinBox`) ou seletor (`QSlider`).
- **Lógica local de proteção de software:** se a potência calculada ultrapassar o setpoint configurado, o software muda a cor do dashboard para amarelo/vermelho, emite alerta visual e registra a ocorrência de sobrecorrente.

## 4. Gestão de histórico e auditoria (logs em tabela)

Toda a atividade do sistema é centralizada numa `QTableWidget` de registros:

| Coluna | Descrição do dado | Exemplo de preenchimento |
|---|---|---|
| Data / Hora | Carimbo de data/hora exato do evento (timestamp) | 10/08/2026 10:30:15 |
| Tipo de Evento | Categoria do evento registrado | Comando, Alerta ou Status |
| Descrição | Detalhes do evento ou valor medido na ocorrência | Corte de emergência acionado via software |
| Valor Medido | Potência/Corrente no momento do evento | 12,5 A / 2750 W |

## Opção de tema livre (prototipagem de microcontroladores)

Equipes que preferirem podem aplicar o software supervisor a um protótipo físico/projeto desenvolvido em disciplinas como Microcontroladores, Microprocessadores ou Sistemas Embarcados, desde que o projeto atenda aos mesmos requisitos de leitura analógica/digital e acionamento de atuadores. O SkyVolt usa essa opção: o "microcontrolador" é o ESP32 #2 (telemetria/LoRa, ver [`firmware/esp32-telemetry/`](../firmware/esp32-telemetry/)), e o disjuntor/relé é simulado pelo módulo de segurança embarcado no drone até a integração real (Unidade 4, ver [`ideias/roadmap.md`](../ideias/roadmap.md)).
