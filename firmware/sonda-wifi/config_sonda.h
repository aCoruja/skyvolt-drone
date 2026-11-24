#ifndef SKYVOLT_CONFIG_SONDA_H
#define SKYVOLT_CONFIG_SONDA_H

#include <stddef.h>
#include <stdint.h>

// --- Wi-Fi ---------------------------------------------------------------
// Deixe WIFI_SSID vazio para a placa criar a própria rede (modo AP).
// Não commite senhas reais da sua rede.
#define WIFI_SSID ""
#define WIFI_SENHA ""
#define AP_SSID "SkyVolt-Sonda"
#define AP_SENHA "skyvolt123"  // WPA2 exige no mínimo 8 caracteres
#define NOME_MDNS "skyvolt-sonda"  // modo estação: skyvolt-sonda.local
constexpr uint32_t WIFI_TIMEOUT_MS = 15000;
constexpr uint16_t PORTA_TCP = 3333;

// --- Pinos (ESP32 Dev Module / DevKit V1, ESP32-WROOM-32) -----------------------
// Só ADC1 (GPIO32-39): o ADC2 não funciona com o Wi-Fi ligado.
// Circuito montado na protoboard: divisor R1 470R / R2 12R no
// GPIO32, shunt Rs 0,47R no GPIO34 e o MOSFET Q1 comandado pelo GPIO26.
constexpr bool MEDE_CORRENTE = true;   // false: só o divisor, sem shunt nem chave
constexpr int PINO_ADC_I = 34;    // ADC1_CH6, topo do shunt Rs 0,47R
constexpr int PINO_ADC_VDC = 32;  // ADC1_CH4, meio do divisor R1 470R / R2 12R (5 W)
constexpr int PINO_K2 = 26;      // gate do Q1 IRLZ44N (100R, 10k para o GND) = disjuntor do app; GPIO5 é pino de boot

// --- Tempos ----------------------------------------------------------------
constexpr uint32_t ASSENTAMENTO_RELE_MS = 2;   // K2 é MOSFET (comuta em µs): só o tempo de a corrente assentar
constexpr uint32_t TIMEOUT_LINK_MS = 6000;     // sem comando do app -> abre K2
constexpr uint32_t RENOVAR_TENSAO_MS = 10000;  // com K2 fechado, abre K2 brevemente para medir V (0 = nunca)
constexpr uint32_t INTERVALO_PADRAO_MS = 2000;
constexpr uint32_t INTERVALO_MINIMO_MS = 300;
constexpr size_t AMOSTRAS = 400;               // 400 x 500 us = 200 ms (12 ciclos de 60 Hz)
constexpr uint32_t PERIODO_AMOSTRA_US = 500;

// --- Conversão (valores nominais; calibrar pela USB, ver README) --------------
// 12 V -> 0,30 V e 24 V -> 0,60 V no ADC; abaixo de ~6 V lê 0. Só DC.
constexpr double FATOR_DIVISOR_DC = (470.0 + 12.0) / 12.0;  // R1/R2
constexpr double R_SHUNT_OHM = 0.47;           // Rs 5 W: 1 A -> 0,47 V no GPIO34
// Teto do ADC (atenuação 11 dB).
constexpr double ADC_MAX_VALIDO_MV = 3050.0;
constexpr double ADC_MIN_VALIDO_MV = 30.0;
// Piso do ADC do ESP32 clássico: abaixo de ~0,1 V a leitura crua é 0 e analogReadMilliVolts devolve
// ~142 mV (medido no GPIO32 com o pino em 0 V). No divisor DC isso viraria 5,7 V fantasma: média até
// este valor conta como 0 V, então a sonda só enxerga DC a partir de ~6 V (24 V -> 0,6 V, bem acima).
constexpr double ADC_PISO_MV = 150.0;

// --- Disparo por sobrecorrente (proteção local, sem esperar o app) ----------------
// Com K2 fechada a sonda é um curto entre os pés: quem limita a corrente é a carga em série no fio.
// O Rs tira tensão do gate do Q1 (Vgs = 3,3 V - I x 0,47): num curto o Q1 se autolimita perto de 2-4 A
// e esquenta, então o limite fica bem abaixo disso para garantir o disparo.
constexpr double LIMITE_DISPARO_A = 1.5;
constexpr int AMOSTRAS_DISPARO = 3;        // leituras seguidas acima do limite (filtra ruído do ADC)

#endif
