#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11
#define LED_PIN 3
#define BUZZER_PIN 4

DHT dht(DHTPIN, DHTTYPE);

float tempThreshold = 40.0;
float humThreshold = 70.0;
int gasThreshold = 800;
int gasPin = A0;

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  int gasValue = analogRead(gasPin);

  Serial.print(temperature);
  Serial.print(",");
  Serial.print(humidity);
  Serial.print(",");
  Serial.println(gasValue);
  
  if (temperature > tempThreshold || humidity > humThreshold || gasValue > gasThreshold) {
    digitalWrite(LED_PIN, HIGH);
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
  }

  delay(2000);
}
