const int sampling_frequency = 9000;      // Number of samples per second
const int serialBaudRate = 19200;
int sensorPin = A1;

void setup() {
  Serial.begin(serialBaudRate);
}

void loop() {
  int tenBitValue = analogRead(sensorPin);
  byte eightBitValue = tenBitValue / 4;
  Serial.write(eightBitValue);
  delayMicroseconds(1000000 / sampling_frequency);  // Delay between samples
}