#ifndef SKYVOLT_PROCESSAMENTO_H
#define SKYVOLT_PROCESSAMENTO_H

#include "medicao.h"

struct ConfigMedicao {
  bool calibracao_validada, canal_bipolar;
  double ganho_v, offset_v, ganho_i, offset_i;
  double adc_min_mv, adc_max_mv, taxa_hz, minimo_sinal, ripple_dc;
  double histerese, freq_min, freq_max;
};

struct ResultadoMedicao {
  TipoSinal tipo;
  double v, i, p;
};

// Buffers mutáveis são convertidos de mV de ADC para grandezas físicas.
inline bool processar(double *v, double *i, size_t n, const ConfigMedicao &c,
                      ResultadoMedicao &saida) {
  saida.tipo = TipoSinal::Indeterminado;
  if (!c.calibracao_validada || !c.canal_bipolar || !v || !i || n < 4 ||
      !isfinite(c.ganho_v) || !isfinite(c.offset_v) ||
      !isfinite(c.ganho_i) || !isfinite(c.offset_i) ||
      c.ganho_v == 0 || c.ganho_i == 0 || !isfinite(c.adc_min_mv) ||
      !isfinite(c.adc_max_mv) || c.adc_min_mv >= c.adc_max_mv) return false;
  for (size_t k = 0; k < n; ++k) {
    if (!isfinite(v[k]) || !isfinite(i[k]) || v[k] <= c.adc_min_mv ||
        v[k] >= c.adc_max_mv || i[k] <= c.adc_min_mv || i[k] >= c.adc_max_mv)
      return false;
    v[k] = c.ganho_v * v[k] + c.offset_v;
    i[k] = c.ganho_i * i[k] + c.offset_i;
  }
  Estatisticas e{};
  if (!calcular_medicao(v, i, n, e)) return false;
  saida.tipo = classificar_sinal(v, n, c.taxa_hz, c.minimo_sinal, c.ripple_dc,
                                 c.histerese, c.freq_min, c.freq_max);
  if (saida.tipo == TipoSinal::Indeterminado) return false;
  saida.v = saida.tipo == TipoSinal::AC ? e.rms_v : e.media_v;
  saida.i = saida.tipo == TipoSinal::AC ? e.rms_i : e.media_i;
  saida.p = e.potencia;
  return true;
}

#endif
