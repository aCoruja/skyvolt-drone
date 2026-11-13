#include <Arduino.h>
#include "configuracao.h"

constexpr int PINO_TENSAO = 1, PINO_CORRENTE = 2;
constexpr size_t AMOSTRAS = 400;
constexpr uint32_t PERIODO_US = 500;
static double v[AMOSTRAS], i[AMOSTRAS];

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PINO_TENSAO, ADC_11db);
  analogSetPinAttenuation(PINO_CORRENTE, ADC_11db);
}

void loop() {
  uint32_t soma_v = 0, soma_i = 0;
  bool atrasou = false;
  uint32_t proxima = micros();
  for (size_t k = 0; k < AMOSTRAS; ++k) {
    while (static_cast<int32_t>(micros() - proxima) < 0) delayMicroseconds(10);
    if (static_cast<int32_t>(micros() - proxima) > 100) atrasou = true;
    v[k] = analogReadMilliVolts(PINO_TENSAO);
    i[k] = analogReadMilliVolts(PINO_CORRENTE);
    soma_v += static_cast<uint32_t>(v[k]);
    soma_i += static_cast<uint32_t>(i[k]);
    proxima += PERIODO_US;
  }
  ResultadoMedicao resultado{};
  // A aquisição é sequencial. Verificar tempo e fase em bancada antes de ativar.
  bool valido = !atrasou && TEMPORIZACAO_VALIDADA &&
                processar(v, i, AMOSTRAS, CONFIG, resultado);
  Serial.print("{\"t\":");
  Serial.print(static_cast<uint32_t>(millis()));
  if (valido) {
    Serial.print(",\"estado\":\"OK\",\"tipo\":\"");
    Serial.print(resultado.tipo == TipoSinal::AC ? "AC" : "DC");
    Serial.print("\",\"v\":"); Serial.print(resultado.v, 6);
    Serial.print(",\"i\":"); Serial.print(resultado.i, 6);
    Serial.print(",\"p\":"); Serial.print(resultado.p, 6);
  } else {
    Serial.print(",\"estado\":\"ERRO\",\"tipo\":null,\"v\":null,\"i\":null,\"p\":null");
  }
  Serial.print(",\"adc_v_mv\":"); Serial.print(soma_v / AMOSTRAS);
  Serial.print(",\"adc_i_mv\":"); Serial.print(soma_i / AMOSTRAS);
  Serial.println("}");
  delay(800);
}
