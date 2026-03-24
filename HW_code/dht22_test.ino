void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("=== Soil Moisture Sensor Test ===");
  Serial.println("Hold sensor in AIR... then dip in WATER");
  Serial.println("=================================");
}

void loop() {
  int rawValue = analogRead(34);
  
  Serial.print("Raw ADC: ");
  Serial.print(rawValue);
  
  if (rawValue == 0) {
    Serial.println("  ⚠️  Reading 0 — check wiring!");
  } else if (rawValue > 2500) {
    Serial.println("  → DRY (in air)");
  } else if (rawValue < 1500) {
    Serial.println("  → WET (in water)");
  } else {
    Serial.println("  → MOIST (in soil)");
  }
  
  delay(1000);
}