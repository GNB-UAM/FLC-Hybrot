
int lightPin = 1;

void setup() {
  Serial.begin(19200);
}

void loop() {
  Serial.println(analogRead(lightPin));
  delay(100);
}
