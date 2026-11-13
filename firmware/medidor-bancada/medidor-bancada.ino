#include <Arduino.h>
#include "medicao.h"

// Aquisição de diagnóstico, somente após revisão do circuito de baixa tensão.
// Valores físicos permanecem nulos até calibração e validação reais.
constexpr int PINO_TENSAO = 1;
constexpr int PINO_CORRENTE = 2;
constexpr int AMOSTRAS = 32;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PINO_TENSAO, ADC_11db);
  analogSetPinAttenuation(PINO_CORRENTE, ADC_11db);
}

void loop() {
  uint32_t soma_v = 0, soma_i = 0;
  for (int k = 0; k < AMOSTRAS; ++k) {
    soma_v += analogReadMilliVolts(PINO_TENSAO);
    soma_i += analogReadMilliVolts(PINO_CORRENTE);
    delay(1);
  }
  Serial.print("{\"t\":");
  Serial.print((uint32_t)millis());
  Serial.print(",\"estado\":\"ERRO\",\"tipo\":null,\"v\":null,\"i\":null,\"p\":null,\"adc_v_mv\":");
  Serial.print(soma_v / AMOSTRAS);
  Serial.print(",\"adc_i_mv\":");
  Serial.print(soma_i / AMOSTRAS);
  Serial.println("}");
  delay(1000);
}
