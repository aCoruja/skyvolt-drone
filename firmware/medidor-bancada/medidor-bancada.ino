#include <Arduino.h>
#include "medicao.h"

// O hardware e a calibração ainda não foram identificados. Por segurança,
// este firmware não lê entradas nem apresenta valores de medição simulados.
void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.print("{\"t\":");
  Serial.print((uint32_t)millis());
  Serial.println(",\"estado\":\"ERRO\",\"tipo\":null,\"v\":null,\"i\":null,\"p\":null}");
  delay(1000);
}
