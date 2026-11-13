#include "../firmware/medidor-bancada/processamento.h"
#include <cassert>
#include <cmath>

int main() {
  ConfigMedicao c{false, true, 0.01, -10, 0.01, -10,
                  -1, 3000, 2000, 2, 0.1, 0.5, 55, 65};
  double v[400], i[400];
  for (int k = 0; k < 400; ++k) { v[k] = 2200; i[k] = 1200; }
  ResultadoMedicao r{};
  assert(!processar(v, i, 400, c, r));
  c.calibracao_validada = true;
  assert(processar(v, i, 400, c, r));
  assert(r.tipo == TipoSinal::DC);
  assert(std::fabs(r.v - 12) < 1e-9 && std::fabs(r.i - 2) < 1e-9);
  assert(std::fabs(r.p - 24) < 1e-9);
  for (int k = 0; k < 400; ++k) {
    double onda = std::sin(2 * 3.141592653589793 * 60 * k / 2000);
    v[k] = 1000 + 1000 * onda; i[k] = 1000 + 200 * onda;
  }
  assert(processar(v, i, 400, c, r));
  assert(r.tipo == TipoSinal::AC && std::fabs(r.p - 10) < 1e-8);
  for (int k = 0; k < 400; ++k) { v[k] = 2200; i[k] = 1200; }
  v[0] = 3000;
  assert(!processar(v, i, 400, c, r));
  c.canal_bipolar = false;
  assert(!processar(v, i, 400, c, r));
}
