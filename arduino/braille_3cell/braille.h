#ifndef BRAILLE_H
#define BRAILLE_H

#include <Arduino.h>

class braille {
private:
  int dataPin;
  int latchPin;
  int clockPin;
  int no_module;
  byte* cellBuffer;

public:
  braille(int dataPin, int latchPin, int clockPin, int no_module);
  ~braille();
  void begin();
  void all_off();
  void refresh();
  void on(int module, int dot);
  void off(int module, int dot);
};

#endif

