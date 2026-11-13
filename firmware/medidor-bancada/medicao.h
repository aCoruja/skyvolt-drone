#ifndef SKYVOLT_MEDICAO_H
#define SKYVOLT_MEDICAO_H

#include <math.h>
#include <stddef.h>

// Entradas já calibradas em volts e ampères e amostradas em instantes comuns.
struct Estatisticas {
  double media_v, media_i, rms_v, rms_i, rms_ac_v, potencia, aparente;
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
  r.aparente = r.rms_v * r.rms_i;
  return isfinite(r.media_v) && isfinite(r.media_i) && isfinite(r.rms_v) &&
         isfinite(r.rms_i) && isfinite(r.rms_ac_v) &&
         isfinite(r.potencia) && isfinite(r.aparente);
}

enum class TipoSinal { Indeterminado, AC, DC };

// Classificação experimental de tensão já calibrada, sem saturação, amostrada
// uniformemente. Só chamar quando o canal puder medir DC e ambos semiciclos.
// Limiares e faixa de frequência precisam ser validados para o equipamento.
inline TipoSinal classificar_sinal(const double *v, size_t n, double taxa_hz,
                                   double minimo_sinal, double maximo_ripple_dc,
                                   double histerese, double freq_min,
                                   double freq_max) {
  if (!v || n < 4 || !isfinite(taxa_hz) || !isfinite(minimo_sinal) ||
      !isfinite(maximo_ripple_dc) || !isfinite(histerese) ||
      !isfinite(freq_min) || !isfinite(freq_max) || taxa_hz <= 0 ||
      minimo_sinal <= 0 || maximo_ripple_dc < 0 || histerese <= 0 ||
      freq_min <= 0 || freq_max <= freq_min || taxa_hz <= 2 * freq_max)
    return TipoSinal::Indeterminado;
  double soma = 0;
  for (size_t k = 0; k < n; ++k) {
    if (!isfinite(v[k])) return TipoSinal::Indeterminado;
    soma += v[k];
  }
  double media = soma / n, soma2 = 0;
  if (!isfinite(media)) return TipoSinal::Indeterminado;
  int lado = 0;
  size_t cruzamentos = 0;
  for (size_t k = 0; k < n; ++k) {
    double d = v[k] - media;
    soma2 += d * d;
    int novo = d > histerese ? 1 : (d < -histerese ? -1 : 0);
    if (novo && lado && novo != lado) ++cruzamentos;
    if (novo) lado = novo;
  }
  double ripple = sqrt(soma2 / n);
  if (!isfinite(ripple)) return TipoSinal::Indeterminado;
  // Exigir janela suficientemente longa para estimar mais de dois ciclos.
  double duracao = (n - 1) / taxa_hz;
  if (duracao < 2.0 / freq_min) return TipoSinal::Indeterminado;
  if (ripple <= maximo_ripple_dc && fabs(media) >= minimo_sinal)
    return TipoSinal::DC;
  double frequencia = cruzamentos / (2.0 * duracao);
  if (ripple >= minimo_sinal && cruzamentos >= 4 &&
      frequencia >= freq_min && frequencia <= freq_max &&
      fabs(media) < minimo_sinal)
    return TipoSinal::AC;
  return TipoSinal::Indeterminado;
}

#endif
