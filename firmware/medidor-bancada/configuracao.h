#ifndef SKYVOLT_CONFIGURACAO_H
#define SKYVOLT_CONFIGURACAO_H
#include "processamento.h"

// Exemplos para desenvolvimento; não são calibração ou validação.
constexpr bool TEMPORIZACAO_VALIDADA = false;
const ConfigMedicao CONFIG = {
    false, false, 1.0, 0.0, 1.0, 0.0,
    100.0, 3000.0, 2000.0, 2.0, 0.1, 0.5, 55.0, 65.0
};
#endif
