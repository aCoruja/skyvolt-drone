# Firmware da sonda Wi-Fi (ESP32 Dev Module)

Liga a sonda de pouso ao app desktop por Wi-Fi. Fala o mesmo JSON por linha do serial ([protocolo de telemetria](../../docs/protocolo_telemetria.md)) num servidor TCP na porta 3333.

Circuito de bancada simples, só DC, sem módulos: divisor de tensão R1 470 Ω / R2 12 Ω (5 W), shunt Rs 0,47 Ω (5 W) para a corrente e um MOSFET (Q1) no lado do GND como chave do disjuntor. Pinos em `config_sonda.h`.

**Só para bancada com fonte isolada, até 24 V DC, com carga em série.** O GND do ESP32 fica ligado ao PÉ B, então isto não atende ao RNF02 nem serve para a rede elétrica.

| No app | Na sonda |
|---|---|
| Disjuntor (Corte Emergencial / Religar) | Q1 comandado pelo GPIO26: fecha o fio aberto passando pelo shunt |
| Tensão, corrente, potência e gráfico | ADC1 do ESP32: GPIO32 = divisor, GPIO34 = shunt |
| Card WIFI: Conectar/Desconectar | Servidor TCP + handshake |

## Ligações

| De | Para |
|---|---|
| PÉ A (+ da fonte, com carga em série) | R1 470 Ω e dreno (D) do Q1 |
| Meio do divisor (R1/R2) | GPIO32 |
| Fonte (S) do Q1 | Rs 0,47 Ω e, por 1 kΩ, o GPIO34 |
| R2, Rs e PÉ B (− da fonte) | GND do ESP32 |
| GPIO26 | gate do Q1 (direto com MOSFET de nível lógico IRL…, ou pelo driver NPN+PNP com IRFZ34N) |

O **GND do ESP32 precisa estar ligado ao − da fonte**. Sem isso a corrente do divisor passa pelos diodos de proteção do ESP32 e as leituras grudam no teto do ADC.

## Gravar

1. Arduino IDE ou `arduino-cli` com o core **esp32 by Espressif 3.x**, placa **ESP32 Dev Module** (DevKit V1, ESP32-WROOM-32). Não usa bibliotecas externas.
2. Rede: em `config_sonda.h`, deixe `WIFI_SSID` vazio e a placa cria a rede **SkyVolt-Sonda** (senha `skyvolt123`, IP `192.168.4.1`). Para usar a rede do laboratório, preencha `WIFI_SSID`/`WIFI_SENHA`, mas não commite a senha. O IP aparece no monitor serial (115200 bps). Se a rede não responder em 15 s, a placa volta a criar a própria rede.
3. Pela linha de comando, a partir da raiz do repositório:
   ```sh
   arduino-cli compile --fqbn esp32:esp32:esp32 firmware/sonda-wifi
   arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/sonda-wifi
   ```

## Usar com o app

`python -m app.main` → card **WIFI** → **Conectar** → `192.168.4.1:3333` (o endereço fica salvo em `app/data/config.json`). Depois do handshake, o app envia o estado do disjuntor gravado no banco. Selecione o modo **DC**.

## Como mede

- **Fio aberto e só dois pés:** com o Q1 fechado, os pés ficam em curto e a tensão entre eles cai a ~0 V. Por isso a tensão é medida com o Q1 aberto (é a tensão da fonte) e fica guardada. Com o disjuntor fechado, a cada 10 s (`RENOVAR_TENSAO_MS`) o Q1 abre por ~200 ms para medir de novo; ponha `0` para desligar.
- **Corrente:** I = tensão no shunt / 0,47 Ω. Lê de ~0,3 A (piso do ADC) a ~1,5 A.
- **Potência:** P = V × I, com V e I medidos em momentos diferentes.
- **Tensão:** V = tensão no GPIO32 × 40,2. Abaixo de ~6 V (0,15 V no pino) o ADC do ESP32 não distingue de 0 V, então a sonda informa 0 V. O divisor fica sempre entre os pés: ~25 mA passam pela carga mesmo com o Q1 aberto. Calibre com `cal vdc` usando a carga real.
- **Estado seguro:** ao ligar, o Q1 fica aberto. Se o app fechar o socket ou ficar 6 s sem enviar comando (ele manda `PING` a cada 2 s), a placa abre o Q1. Ao reconectar, o app reenvia o estado do disjuntor.
- **Disparo por sobrecorrente:** o firmware vigia o shunt o tempo todo com o Q1 fechado e, com 3 leituras seguidas acima de 1,5 A (ou o ADC no teto), abre o Q1 sozinho e manda `{"ack":"RELE","estado":"ABERTO","motivo":"SOBRECORRENTE","i":…}`. O app abre o disjuntor e grava o evento. **Nunca ligue a fonte direto nos pés sem carga em série.**

## Comandos pelo monitor serial (115200 bps)

| Comando | Condição | O que faz |
|---|---|---|
| `info` | — | mostra K2, IP e coeficientes |
| `adc` | — | leitura crua (mV) do GPIO32 e do GPIO34 |
| `k2 1` / `k2 0` | — | fecha/abre o Q1 sem o app (bancada) |
| `cal vdc 12.0` | Q1 aberto | ajusta o divisor para a leitura do multímetro |
| `cal i 0.50` | Q1 fechado com carga | ajusta o shunt |
| `padrao` | — | volta aos valores nominais |

Os coeficientes ficam salvos na flash (Preferences).
