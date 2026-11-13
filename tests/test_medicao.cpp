#include "../firmware/medidor-bancada/medicao.h"
#include <assert.h>
#include <cmath>
#include <limits>

int main() {
  Estatisticas r{};
  double vdc[] = {12, 12, 12, 12}, idc[] = {2, 2, 2, 2};
  assert(calcular_medicao(vdc, idc, 4, r));
  assert(std::fabs(r.media_v - 12) < 1e-10);
  assert(std::fabs(r.rms_ac_v) < 1e-10);
  assert(std::fabs(r.potencia - 24) < 1e-10);

  double v[] = {1, 0, -1, 0}, i[] = {0, 1, 0, -1};
  assert(calcular_medicao(v, i, 4, r));
  assert(std::fabs(r.rms_v - std::sqrt(0.5)) < 1e-10);
  assert(std::fabs(r.potencia) < 1e-10); // 90 graus de defasagem
  assert(calcular_medicao(v, v, 4, r));
  assert(std::fabs(r.potencia - 0.5) < 1e-10);
  assert(std::fabs(r.aparente - 0.5) < 1e-10);
  assert(!calcular_medicao(nullptr, i, 4, r));
  assert(!calcular_medicao(v, i, 1, r));
  double invalido[] = {0, std::numeric_limits<double>::quiet_NaN()};
  assert(!calcular_medicao(invalido, invalido, 2, r));
  double sinal[400], zero[400] = {};
  for (int k = 0; k < 400; ++k)
    sinal[k] = 12 * std::sin(2 * 3.141592653589793 * 60 * k / 2000);
  assert(classificar_sinal(sinal, 400, 2000, 2, 0.1, 0.5, 55, 65) == TipoSinal::AC);
  for (double &amostra : sinal) amostra = 12;
  assert(classificar_sinal(sinal, 400, 2000, 2, 0.1, 0.5, 55, 65) == TipoSinal::DC);
  assert(classificar_sinal(zero, 400, 2000, 2, 0.1, 0.5, 55, 65) == TipoSinal::Indeterminado);
  assert(classificar_sinal(sinal, 4, 2000, 2, 0.1, 0.5, 55, 65) == TipoSinal::Indeterminado);
  assert(classificar_sinal(sinal, 400, 2000, 2, 0.1, 0.5, 65, 55) == TipoSinal::Indeterminado);
}
