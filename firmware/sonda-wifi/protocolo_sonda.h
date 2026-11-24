#ifndef SKYVOLT_PROTOCOLO_SONDA_H
#define SKYVOLT_PROTOCOLO_SONDA_H

// JSON por linha, mesmo contrato do serial (docs/protocolo_telemetria.md).
// O app só envia objetos planos e pequenos, então basta localizar a chave.

#include <ctype.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Ponteiro para o primeiro caractere do valor de "chave", ou nullptr.
inline const char *valor_da_chave(const char *linha, const char *chave) {
  if (!linha || !chave) return nullptr;
  char padrao[24];
  int n = snprintf(padrao, sizeof padrao, "\"%s\"", chave);
  if (n <= 0 || static_cast<size_t>(n) >= sizeof padrao) return nullptr;
  const char *p = strstr(linha, padrao);
  if (!p) return nullptr;
  p += n;
  while (isspace(static_cast<unsigned char>(*p))) ++p;
  if (*p != ':') return nullptr;
  ++p;
  while (isspace(static_cast<unsigned char>(*p))) ++p;
  return p;
}

inline bool campo_texto(const char *linha, const char *chave, char *saida, size_t tam) {
  const char *p = valor_da_chave(linha, chave);
  if (!p || *p != '"' || !saida || tam == 0) return false;
  ++p;
  size_t k = 0;
  while (*p && *p != '"') {
    if (k + 1 >= tam) return false;
    saida[k++] = *p++;
  }
  if (*p != '"') return false;
  saida[k] = '\0';
  return true;
}

inline bool campo_numero(const char *linha, const char *chave, double &valor) {
  const char *p = valor_da_chave(linha, chave);
  if (!p) return false;
  char *fim = nullptr;
  double v = strtod(p, &fim);
  if (fim == p || !isfinite(v)) return false;
  valor = v;
  return true;
}

// Grandezas inválidas viram null, nunca zero.
inline void formatar_numero(char *buf, size_t tam, double v) {
  if (isfinite(v))
    snprintf(buf, tam, "%.3f", v);
  else
    snprintf(buf, tam, "null");
}

inline int formatar_telemetria(char *buf, size_t tam, uint32_t t, bool valido, const char *tipo,
                               double v, double i, double p, bool rele_fechado) {
  const char *rele = rele_fechado ? "FECHADO" : "ABERTO";
  if (!valido)
    return snprintf(buf, tam,
                    "{\"t\":%lu,\"estado\":\"ERRO\",\"tipo\":null,\"v\":null,\"i\":null,"
                    "\"p\":null,\"rele\":\"%s\"}\n",
                    static_cast<unsigned long>(t), rele);
  char sv[16], si[16], sp[16];
  formatar_numero(sv, sizeof sv, v);
  formatar_numero(si, sizeof si, i);
  formatar_numero(sp, sizeof sp, p);
  return snprintf(buf, tam,
                  "{\"t\":%lu,\"estado\":\"OK\",\"tipo\":\"%s\",\"v\":%s,\"i\":%s,\"p\":%s,"
                  "\"rele\":\"%s\"}\n",
                  static_cast<unsigned long>(t), tipo, sv, si, sp, rele);
}

#endif
