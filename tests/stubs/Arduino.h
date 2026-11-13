#ifndef TEST_ARDUINO_H
#define TEST_ARDUINO_H
#include <cstddef>
#include <cstdint>

constexpr int ADC_11db = 3;
struct SerialTeste {
  void begin(int) {}
  template <typename T> void print(T) {}
  void print(double, int) {}
  void println(const char *) {}
};
extern SerialTeste Serial;
void analogReadResolution(int);
void analogSetPinAttenuation(int, int);
uint32_t analogReadMilliVolts(int);
uint32_t micros();
uint32_t millis();
void delayMicroseconds(unsigned int);
void delay(unsigned int);
#endif
