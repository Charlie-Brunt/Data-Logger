#include <math.h>

const int amplitude = 127;     // Amplitude of the sine wave (0-255)
const int frequency = 1000;     // Frequency of the sine wave (Hz)
const int sampling_frequency = 9000;      // Number of samples per second
const int serialBaudRate = 19200;

void setup() {
  Serial.begin(serialBaudRate);
}

void loop() {
  for (int i = 0; i < sampling_frequency; i++) {
    float value = sin(2 * PI * frequency * i / sampling_frequency)/1.3 + 0.3*sin(2 * PI * 4 * frequency * i / sampling_frequency)/1.3;
    int output = amplitude * value + 128;  // Map the sine wave to the range 0-255

    Serial.write(output);
    delayMicroseconds(1000000 / sampling_frequency);  // Delay between samples
  }
}