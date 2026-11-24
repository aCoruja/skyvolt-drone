#ifndef SKYVOLT_MEDICAO_SONDA_H
#define SKYVOLT_MEDICAO_SONDA_H

#include <math.h>

#include "config_sonda.h"

// Estatísticas de uma janela de amostras em mV do ADC.
struct Janela {
  double media, rms_ac, minimo, maximo;
};

inline bool estatisticas(const float *mv, size_t n, Janela &j) {
  if (!mv || n < 2) return false;
  double soma = 0, soma2 = 0;
  j.minimo = j.maximo = mv[0];
  for (size_t k = 0; k < n; ++k) {
    soma += mv[k];
    soma2 += static_cast<double>(mv[k]) * mv[k];
    j.minimo = fmin(j.minimo, mv[k]);
    j.maximo = fmax(j.maximo, mv[k]);
  }
  j.media = soma / n;
  // RMS só da componente alternada (média da janela removida).
  j.rms_ac = sqrt(fmax(0.0, soma2 / n - j.media * j.media));
  return isfinite(j.media) && isfinite(j.rms_ac);
}

// No divisor DC, 0 V na sonda é leitura legítima perto de 0 mV: só o topo indica saturação.
inline bool saturado(const Janela &j, bool so_topo) {
  if (j.maximo >= ADC_MAX_VALIDO_MV) return true;
  return !so_topo && j.minimo <= ADC_MIN_VALIDO_MV;
}

inline double tensao_dc(double media_mv, double cal) {
  if (media_mv <= ADC_PISO_MV) return 0.0;  // piso do ADC: o pino está em ~0 V
  return media_mv / 1000.0 * FATOR_DIVISOR_DC * cal;
}

// Corrente pelo shunt (I = V / Rs). Até o piso do ADC (~0,32 A) a leitura é 0.
inline double corrente_bruta(double mv, double cal) {
  return mv / 1000.0 / R_SHUNT_OHM * cal;
}

inline double corrente_shunt(double media_mv, double cal) {
  if (media_mv <= ADC_PISO_MV) return 0.0;
  return corrente_bruta(media_mv, cal);
}

// Uma leitura instantânea do shunt acima do limite de disparo (ou o ADC no teto).
inline bool sobrecorrente(double mv, double cal) {
  return mv >= ADC_MAX_VALIDO_MV || corrente_bruta(mv, cal) >= LIMITE_DISPARO_A;
}

#endif
