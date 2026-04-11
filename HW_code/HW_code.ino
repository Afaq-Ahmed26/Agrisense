#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

const int SOIL_MOISTURE_PIN = 34;

const char* WIFI_SSID     = "Agrisense";
const char* WIFI_PASSWORD = "passwordd";
const char* API_BASE_URL  = "http://192.168.43.120:8000";

// ⚠️ We will update these after seeing raw values
const int SOIL_MOISTURE_DRY = 2950;
const int SOIL_MOISTURE_WET = 1250;

const unsigned long SENSOR_READ_INTERVAL_MS = 2000;
unsigned long lastReadTime = 0;

float soilMoisture = 0.0;
String deviceId = "";

void setupWifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void generateDeviceId() {
  uint64_t chipid = ESP.getEfuseMac();
  deviceId = "esp32-" + String((uint32_t)(chipid >> 24), HEX);
  Serial.print("Device ID: ");
  Serial.println(deviceId);
}

float readSoilMoisture() {
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  
  // 🔍 CALIBRATION: Print raw value so we can set correct min/max
  Serial.print("Raw ADC Value: ");
  Serial.println(rawValue);
  Serial.println("  → Hold sensor in AIR and note this value (DRY)");
  Serial.println("  → Dip sensor in WATER and note this value (WET)");

  int percentage = map(rawValue, SOIL_MOISTURE_DRY, SOIL_MOISTURE_WET, 0, 100);
  return constrain(percentage, 0, 100);
}

void printReadings() {
  Serial.println("\n--- AgriSense Status ---");
  Serial.print("Soil Moisture: ");
  Serial.print(soilMoisture);
  Serial.println("%");
}

void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Reconnecting...");
    setupWifi();
    return;
  }

  HTTPClient http;
  String apiUrl = String(API_BASE_URL) + "/sensors/" + deviceId + "/readings";

  Serial.print("Sending to: ");
  Serial.println(apiUrl);

  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  // temperature, humidity, light_level are placeholders until real sensors added
  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\""   + deviceId + "\",";
  jsonPayload += "\"soil_moisture\":" + String(soilMoisture, 2) + ",";
  jsonPayload += "\"temperature\":"   + String(25.0)  + ",";  // placeholder
  jsonPayload += "\"humidity\":"      + String(50.0)  + ",";  // placeholder
  jsonPayload += "\"light_level\":"   + String(300.0);        // placeholder
  jsonPayload += "}";

  Serial.print("Payload: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    Serial.print("HTTP Response: ");
    Serial.println(httpResponseCode);
    if (httpResponseCode == 200 || httpResponseCode == 201) {
      Serial.println("✅ Data sent successfully!");
    }
  } else {
    Serial.print("❌ Error: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
  }

  http.end();
}

void setup() {
  Serial.begin(115200);
  generateDeviceId();
  setupWifi();
}

void loop() {
  unsigned long currentTime = millis();
  if (currentTime - lastReadTime >= SENSOR_READ_INTERVAL_MS) {
    lastReadTime = currentTime;
    soilMoisture = readSoilMoisture();
    printReadings();
    sendDataToBackend();
  }
}