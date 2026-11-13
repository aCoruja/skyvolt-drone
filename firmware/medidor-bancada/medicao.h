#ifndef SKYVOLT_MEDICAO_H
#define SKYVOLT_MEDICAO_H

#include <math.h>
#include <stddef.h>

// Entradas já calibradas em volts e ampères e amostradas em instantes comuns.
struct Estatisticas {
  double media_v, media_i, rms_v, rms_i, rms_ac_v, potencia;
};

inline bool calcular_medicao(const double *v, const double *i, size_t n,
                             Estatisticas &r) {
  if (!v || !i || n < 2) return false;
  double sv = 0, si = 0, sv2 = 0, si2 = 0, sp = 0;
  for (size_t k = 0; k < n; ++k) {
    if (!isfinite(v[k]) || !isfinite(i[k])) return false;
    sv += v[k]; si += i[k]; sv2 += v[k] * v[k];
    si2 += i[k] * i[k]; sp += v[k] * i[k];
  }
  r.media_v = sv / n; r.media_i = si / n;
  r.rms_v = sqrt(sv2 / n); r.rms_i = sqrt(si2 / n);
  // RMS da componente alternada, após remoção da média da janela.
  r.rms_ac_v = sqrt(fmax(0.0, sv2 / n - r.media_v * r.media_v));
  r.potencia = sp / n;
  return isfinite(r.rms_v) && isfinite(r.rms_i) && isfinite(r.potencia);
}

#endif
