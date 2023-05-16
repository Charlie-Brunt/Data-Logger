
int val = 0;

// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(A5, INPUT);
  Serial.begin(9600);
}

// the loop function runs over and over again forever
void loop() {
  val = analogRead(A5);
  Serial.println(val);
  delay(100);
}