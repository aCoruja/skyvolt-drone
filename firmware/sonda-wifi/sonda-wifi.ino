// SkyVolt — sonda de pouso via Wi-Fi (ESP32 Dev Module).
// Servidor TCP com o mesmo JSON por linha do serial: o app conecta, faz o HANDSHAKE,
// recebe telemetria e comanda a chave K2 (disjuntor). Só DC.
// Hardware simples, sem módulos: divisor R1/R2 (tensão), shunt Rs 0,47R (corrente) e um IRLZ44N
// com o gate direto no GPIO26 (chave K2); divisor de potência
// R1/R2 para a tensão DC (pinos em config_sonda.h).

#include <Arduino.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <WiFi.h>

#include "config_sonda.h"
#include "medicao_sonda.h"
#include "protocolo_sonda.h"

static WiFiServer servidor(PORTA_TCP);
static WiFiClient cliente;
static bool tem_cliente = false;
static bool handshake_ok = false;
static Preferences prefs;

static bool rele_fechado = false;
static uint32_t intervalo_ms = INTERVALO_PADRAO_MS;
static uint32_t ultimo_comando_ms = 0;
static uint32_t ultima_telemetria_ms = 0;
static uint32_t ultima_tensao_ms = 0;

static double cal_dc = 1.0;
static double cal_i = 1.0;
static double tensao_cache = NAN;

// Disparo por sobrecorrente: abre o K2 no meio de qualquer espera e avisa o app no próximo loop().
static int leituras_acima = 0;
static bool disparo_pendente = false;
static double corrente_disparo = 0.0;
static void avisar_disparo();

static float amostras_v[AMOSTRAS];
static float amostras_i[AMOSTRAS];
static char linha_tcp[256];
static size_t tam_tcp = 0;
static bool descartando_tcp = false;
static char linha_usb[96];
static size_t tam_usb = 0;

// ------------------------------------------------------------------ chave K2 e canais
static void disparar(double mv) {
  digitalWrite(PINO_K2, LOW);  // primeiro abre, depois registra
  rele_fechado = false;
  leituras_acima = 0;
  disparo_pendente = true;
  corrente_disparo = corrente_bruta(mv, cal_i);
}

// Confere uma leitura do shunt; true se disparou agora.
static bool vigiar_corrente(double mv) {
  if (!MEDE_CORRENTE || !rele_fechado) return false;
  if (!sobrecorrente(mv, cal_i)) {
    leituras_acima = 0;
    return false;
  }
  if (++leituras_acima < AMOSTRAS_DISPARO) return false;
  disparar(mv);
  return true;
}

static void acionar_k2(bool fechar) {
  digitalWrite(PINO_K2, fechar ? HIGH : LOW);
  leituras_acima = 0;
  const uint32_t inicio = millis();
  // Fechando: vigia a corrente durante o assentamento, que é quando um curto aparece.
  while (millis() - inicio < ASSENTAMENTO_RELE_MS) {
    if (fechar && vigiar_corrente(analogReadMilliVolts(PINO_ADC_I))) return;
  }
}

static int pino_tensao() { return PINO_ADC_VDC; }

// ------------------------------------------------------------------ aquisição
static bool amostrar(bool canal_v, bool canal_i) {
  const int pino_v = pino_tensao();
  uint32_t proxima = micros();
  for (size_t k = 0; k < AMOSTRAS; ++k) {
    while (static_cast<int32_t>(micros() - proxima) < 0) {
    }
    if (canal_v) amostras_v[k] = analogReadMilliVolts(pino_v);
    if (canal_i) {
      amostras_i[k] = analogReadMilliVolts(PINO_ADC_I);
      if (vigiar_corrente(amostras_i[k])) return false;  // K2 já aberto: janela descartada
    }
    proxima += PERIODO_AMOSTRA_US;
  }
  return true;
}

// Exige K2 aberta: tensão entre os pés = tensão da fonte.
static bool medir_tensao(double &v) {
  if (!amostrar(true, false)) return false;
  Janela jv{};
  if (!estatisticas(amostras_v, AMOSTRAS, jv) || saturado(jv, true)) return false;
  v = tensao_dc(jv.media, cal_dc);
  return true;
}

static void atualizar_cache_tensao() {
  double v;
  tensao_cache = medir_tensao(v) ? v : NAN;
  ultima_tensao_ms = millis();
}

// Com K2 fechada os pés estão em curto pelo Q1 e o Rs (V ~ 0): abre por ~200 ms para medir.
static void renovar_tensao() {
  acionar_k2(false);
  atualizar_cache_tensao();
  acionar_k2(true);
}

static bool medir_corrente(double &i) {
  if (!MEDE_CORRENTE) {
    i = 0.0;  // circuito só com divisor: não há caminho de corrente
    return true;
  }
  if (!amostrar(false, true)) return false;
  Janela ji{};
  if (!estatisticas(amostras_i, AMOSTRAS, ji) || saturado(ji, true)) return false;
  i = corrente_shunt(ji.media, cal_i);
  return true;
}

// ------------------------------------------------------------------ comandos de estado
static void fechar_rele() {
  if (rele_fechado) return;
  atualizar_cache_tensao();  // tensão da fonte com o fio ainda aberto
  rele_fechado = true;
  acionar_k2(true);
}

static void abrir_rele() {
  rele_fechado = false;
  acionar_k2(false);
}

// ------------------------------------------------------------------ telemetria
static const char *nome_modo() { return "DC"; }  // circuito simples: só DC

static void enviar(const char *texto) {
  if (tem_cliente && cliente.connected()) cliente.print(texto);
}

static void ciclo_medicao() {
  double v = NAN, i = NAN;
  bool ok;
  if (!rele_fechado) {
    atualizar_cache_tensao();
    v = tensao_cache;
    i = 0.0;
    ok = isfinite(v);
  } else {
    if (RENOVAR_TENSAO_MS > 0 && millis() - ultima_tensao_ms >= RENOVAR_TENSAO_MS) renovar_tensao();
    v = tensao_cache;
    ok = medir_corrente(i) && isfinite(v);
  }
  avisar_disparo();  // disparo durante a janela: o app sabe antes da telemetria
  char buf[200];
  formatar_telemetria(buf, sizeof buf, millis(), ok, nome_modo(), v, i, ok ? v * i : NAN, rele_fechado);
  if (handshake_ok) enviar(buf);
  Serial.print("# ");
  Serial.print(buf);
}

// ------------------------------------------------------------------ protocolo TCP
static void responder_ack(const char *ack, const char *chave = nullptr, const char *valor = nullptr) {
  char buf[96];
  if (chave)
    snprintf(buf, sizeof buf, "{\"ack\":\"%s\",\"%s\":\"%s\"}\n", ack, chave, valor);
  else
    snprintf(buf, sizeof buf, "{\"ack\":\"%s\"}\n", ack);
  enviar(buf);
}

static void tratar_comando(const char *linha) {
  char cmd[16];
  if (!campo_texto(linha, "cmd", cmd, sizeof cmd)) return;  // linha truncada: ignora
  ultimo_comando_ms = millis();

  if (strcmp(cmd, "HANDSHAKE") == 0) {
    double ms;
    if (campo_numero(linha, "intervalo_ms", ms) && ms >= INTERVALO_MINIMO_MS && ms <= 60000)
      intervalo_ms = static_cast<uint32_t>(ms);
    handshake_ok = true;
    responder_ack("HANDSHAKE");
    Serial.printf("# Handshake: telemetria a cada %lu ms\n", static_cast<unsigned long>(intervalo_ms));
  } else if (strcmp(cmd, "SYNC") == 0) {
    responder_ack("SYNC");  // baud não se aplica ao Wi-Fi
  } else if (strcmp(cmd, "PING") == 0) {
    responder_ack("PING");
  } else if (strcmp(cmd, "RELE") == 0) {
    char estado[12];
    if (!campo_texto(linha, "estado", estado, sizeof estado)) {
      responder_ack("ERRO", "motivo", "RELE sem estado");
    } else if (strcmp(estado, "FECHADO") == 0) {
      fechar_rele();
      if (rele_fechado)
        responder_ack("RELE", "estado", "FECHADO");
      else
        avisar_disparo();  // disparou ao fechar: responde ABERTO com o motivo
    } else if (strcmp(estado, "ABERTO") == 0) {
      abrir_rele();
      responder_ack("RELE", "estado", "ABERTO");
    } else {
      responder_ack("ERRO", "motivo", "estado invalido");
    }
  } else if (strcmp(cmd, "MODO") == 0) {
    char tipo[4];
    if (campo_texto(linha, "tipo", tipo, sizeof tipo) && (!strcmp(tipo, "AC") || !strcmp(tipo, "DC"))) {
      responder_ack("MODO", "tipo", nome_modo());  // só DC: a resposta diz o que a sonda mede
    } else {
      responder_ack("ERRO", "motivo", "tipo invalido");
    }
  } else {
    responder_ack("ERRO", "motivo", "comando desconhecido");
  }
}

// Aviso espontâneo ao app no formato de ACK do RELE (K2), com o motivo (o app abre o disjuntor).
static void avisar_disparo() {
  if (!disparo_pendente) return;
  disparo_pendente = false;
  char buf[112];
  snprintf(buf, sizeof buf, "{\"ack\":\"RELE\",\"estado\":\"ABERTO\",\"motivo\":\"SOBRECORRENTE\",\"i\":%.2f}\n",
           corrente_disparo);
  if (handshake_ok) enviar(buf);
  Serial.printf("# DISPARO: sobrecorrente (~%.2f A, limite %.1f A), K2 aberto\n", corrente_disparo,
                LIMITE_DISPARO_A);
}

static void desconectar_cliente(const char *motivo) {
  Serial.printf("# Link perdido (%s): abrindo K2 por segurança\n", motivo);
  cliente.stop();
  tem_cliente = false;
  handshake_ok = false;
  abrir_rele();
}

static void atender_tcp() {
  WiFiClient novo = servidor.accept();
  if (novo) {
    if (tem_cliente) cliente.stop();  // só um app por vez
    cliente = novo;
    cliente.setNoDelay(true);
    tem_cliente = true;
    handshake_ok = false;
    tam_tcp = 0;
    descartando_tcp = false;
    ultimo_comando_ms = millis();
    Serial.printf("# App conectado: %s\n", cliente.remoteIP().toString().c_str());
  }
  if (!tem_cliente) return;
  if (!cliente.connected()) {
    desconectar_cliente("socket fechado");
    return;
  }
  while (cliente.available()) {
    const char c = static_cast<char>(cliente.read());
    if (c == '\n') {
      if (!descartando_tcp) {
        linha_tcp[tam_tcp] = '\0';
        tratar_comando(linha_tcp);
      }
      tam_tcp = 0;
      descartando_tcp = false;
    } else if (c != '\r') {
      if (tam_tcp + 1 < sizeof linha_tcp)
        linha_tcp[tam_tcp++] = c;
      else
        descartando_tcp = true;  // linha longa demais: descarta até o próximo \n
    }
  }
  if (tem_cliente && millis() - ultimo_comando_ms > TIMEOUT_LINK_MS) desconectar_cliente("sem PING do app");
}

// ------------------------------------------------------------------ calibração pela USB
static void salvar_calibracao() {
  prefs.putDouble("c_dc", cal_dc);
  prefs.putDouble("c_i", cal_i);
}

static void mostrar_info() {
  Serial.printf("# modo=%s K2=%s intervalo=%lu ms\n", nome_modo(), rele_fechado ? "FECHADO" : "ABERTO",
                static_cast<unsigned long>(intervalo_ms));
  Serial.printf("# cal_dc=%.4f cal_i=%.4f (Rs %.2f ohm, disparo %.1f A)\n", cal_dc, cal_i, R_SHUNT_OHM,
                LIMITE_DISPARO_A);
  if (WiFi.getMode() == WIFI_AP)
    Serial.printf("# Wi-Fi AP '%s' IP %s porta %u\n", AP_SSID, WiFi.softAPIP().toString().c_str(), PORTA_TCP);
  else
    Serial.printf("# Wi-Fi '%s' IP %s porta %u\n", WIFI_SSID, WiFi.localIP().toString().c_str(), PORTA_TCP);
}

// Diagnóstico: janela de 200 ms de cada pino, em mV no pino (sem conversão).
static void mostrar_adc() {
  const int pinos[] = {PINO_ADC_VDC, PINO_ADC_I};
  const char *nomes[] = {"VDC (divisor)", "I (shunt)"};
  for (int c = 0; c < 2; ++c) {
    uint32_t proxima = micros();
    for (size_t k = 0; k < AMOSTRAS; ++k) {
      while (static_cast<int32_t>(micros() - proxima) < 0) {
      }
      amostras_v[k] = analogReadMilliVolts(pinos[c]);
      if (pinos[c] == PINO_ADC_I) vigiar_corrente(amostras_v[k]);
      proxima += PERIODO_AMOSTRA_US;
    }
    Janela j{};
    estatisticas(amostras_v, AMOSTRAS, j);
    Serial.printf("# GPIO%d %-13s media=%.0f min=%.0f max=%.0f rms_ac=%.1f mV\n", pinos[c], nomes[c], j.media,
                  j.minimo, j.maximo, j.rms_ac);
  }
}

// Comandos: info | adc | k2 0|1 | cal vdc <V> | cal i <A> | padrao
static void tratar_usb(char *linha) {
  char a[8] = "", b[8] = "";
  double valor = NAN;
  const int n = sscanf(linha, "%7s %7s %lf", a, b, &valor);
  if (n < 1) return;
  if (!strcmp(a, "adc")) {
    mostrar_adc();
  } else if (!strcmp(a, "info")) {
    mostrar_info();
  } else if (!strcmp(a, "k2") && n >= 2) {
    if (!strcmp(b, "1"))
      fechar_rele();
    else
      abrir_rele();
    mostrar_info();
  } else if (!strcmp(a, "padrao")) {
    cal_dc = cal_i = 1.0;
    salvar_calibracao();
    mostrar_info();
  } else if (!strcmp(a, "cal") && n == 3 && valor > 0) {
    Janela j{};
    if (!strcmp(b, "vdc") && !rele_fechado) {
      amostrar(true, false);
      if (estatisticas(amostras_v, AMOSTRAS, j) && j.media > ADC_PISO_MV) cal_dc = valor / tensao_dc(j.media, 1.0);
    } else if (!strcmp(b, "i") && rele_fechado) {
      if (amostrar(false, true) && estatisticas(amostras_i, AMOSTRAS, j)) {
        const double bruta = corrente_shunt(j.media, 1.0);
        if (bruta > 0.01) cal_i = valor / bruta;
      }
    } else {
      Serial.println("# cal vdc: K2 aberta | cal i: K2 fechada");
      return;
    }
    salvar_calibracao();
    mostrar_info();
  } else {
    Serial.println("# comandos: info | adc | k2 0|1 | cal vdc <V> | cal i <A> | padrao");
  }
}

static void atender_usb() {
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n' || c == '\r') {
      if (tam_usb > 0) {
        linha_usb[tam_usb] = '\0';
        tratar_usb(linha_usb);
      }
      tam_usb = 0;
    } else if (tam_usb + 1 < sizeof linha_usb) {
      linha_usb[tam_usb++] = c;
    }
  }
}

// ------------------------------------------------------------------ Wi-Fi
static void iniciar_wifi() {
  WiFi.setHostname(NOME_MDNS);
  bool estacao = false;
  if (strlen(WIFI_SSID) > 0) {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_SENHA);
    const uint32_t inicio = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - inicio < WIFI_TIMEOUT_MS) delay(200);
    estacao = WiFi.status() == WL_CONNECTED;
    if (!estacao) Serial.printf("# Rede '%s' não respondeu: criando AP próprio\n", WIFI_SSID);
  }
  if (estacao) {
    if (MDNS.begin(NOME_MDNS)) MDNS.addService("skyvolt", "tcp", PORTA_TCP);
  } else {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_SENHA);
  }
  WiFi.setSleep(false);
  servidor.begin();
  servidor.setNoDelay(true);
}

void setup() {
  // K2 aberta antes de qualquer outra coisa (estado seguro).
  digitalWrite(PINO_K2, LOW);
  pinMode(PINO_K2, OUTPUT);
  Serial.begin(115200);
  analogReadResolution(12);
  analogSetPinAttenuation(PINO_ADC_VDC, ADC_11db);
  analogSetPinAttenuation(PINO_ADC_I, ADC_11db);

  prefs.begin("sonda", false);
  cal_dc = prefs.getDouble("c_dc", 1.0);
  cal_i = prefs.getDouble("c_i", 1.0);

  delay(ASSENTAMENTO_RELE_MS);
  atualizar_cache_tensao();
  iniciar_wifi();
  mostrar_info();
}

void loop() {
  if (rele_fechado) vigiar_corrente(analogReadMilliVolts(PINO_ADC_I));
  avisar_disparo();
  atender_tcp();
  atender_usb();
  if (millis() - ultima_telemetria_ms >= intervalo_ms) {
    ultima_telemetria_ms = millis();
    ciclo_medicao();
  }
}
