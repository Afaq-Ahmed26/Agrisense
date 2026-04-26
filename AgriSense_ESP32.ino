// =============================================================================
// AgriSense Smart Irrigation System (V4 - Auto Sensor Detection)
//
// Author: Afaq Ahmed
// Date: March 26, 2026
//
// Description:
// Automatically detects which sensors are connected.
// Connected sensors send real values, disconnected ones send default values.
//
// PIN CONFIGURATION:
// Soil Moisture Sensor:
//   VCC  -> 3V3
//   GND  -> GND
//   AOUT -> GPIO34
//
// DHT22 Sensor:
//   +    -> 3V3
//   -    -> GND
//   OUT  -> GPIO4
//
// BH1750 Light Sensor:
//   VCC  -> 3V3
//   GND  -> GND
//   SCL  -> GPIO22
//   SDA  -> GPIO21
//   ADDR -> GND
//
// Relay Module:
//   VCC  -> VIN (5V)
//   GND  -> GND
//   IN   -> GPIO25
// =============================================================================

#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <BH1750.h>
#include <ArduinoJson.h>

// =============================================================================
// Pin Definitions
// =============================================================================
const int SOIL_MOISTURE_PIN = 34;
const int DHT_PIN           = 4;
const int I2C_SDA           = 21;
const int I2C_SCL           = 22;
const int RELAY_PIN         = 25;
const bool RELAY_ACTIVE_LOW = true; // Relay is active-LOW for this module

// =============================================================================
// DHT & BH1750 Setup
// =============================================================================
#define DHTTYPE DHT22
DHT    dht(DHT_PIN, DHTTYPE);
BH1750 lightMeter;

// =============================================================================
// Network Configuration
// =============================================================================
const char* WIFI_SSID     = "Agrisense";
const char* WIFI_PASSWORD = "passwordd";
const char* API_BASE_URLS[] = {
  "http://192.168.100.13:8000", // Primary (home)
  "http://192.168.43.120:8000" // Secondary (current)
};
const int API_BASE_URL_COUNT = sizeof(API_BASE_URLS) / sizeof(API_BASE_URLS[0]);
int activeApiIndex = 0;

// =============================================================================
// Calibration Values
// =============================================================================
const int SOIL_MOISTURE_DRY = 2950;
const int SOIL_MOISTURE_WET = 1250;

// =============================================================================
// Timing
// =============================================================================
const unsigned long SENSOR_READ_INTERVAL_MS = 2000;
const unsigned long SENSOR_REDETECT_INTERVAL_MS = 10000;
unsigned long lastReadTime = 0;
unsigned long lastRedetectTime = 0;

// =============================================================================
// Sensor State Flags
// =============================================================================
bool soilSensorConnected  = false;
bool dhtSensorConnected   = false;
bool lightSensorConnected = false;

// =============================================================================
// Sensor Values
// =============================================================================
float soilMoisture = NAN;
float temperature  = NAN;
float humidity     = NAN;
float lightLevel   = NAN;

String deviceId = "";

void setPumpState(bool on) {
  const int relayLevel = RELAY_ACTIVE_LOW ? (on ? LOW : HIGH) : (on ? HIGH : LOW);
  digitalWrite(RELAY_PIN, relayLevel);
}

// =============================================================================
// WiFi Setup
// =============================================================================
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

// =============================================================================
// Generate Device ID
// =============================================================================
void generateDeviceId() {
  deviceId = "esp32-b47cb8";
  Serial.print("Device ID: ");
  Serial.println(deviceId);
}

// =============================================================================
// Auto-Detect Sensors at Startup
// =============================================================================
void detectSensors() {
  Serial.println("\n--- Detecting Sensors ---");

  // Soil Moisture
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  if (rawValue > 100 && rawValue < 4000) {
    soilSensorConnected = true;
    Serial.println("[OK] Soil Moisture Sensor: CONNECTED");
  } else {
    soilSensorConnected = false;
    Serial.println("[--] Soil Moisture Sensor: NOT CONNECTED");
  }

  // DHT22
  dht.begin();
  delay(2000);
  float testHumidity    = dht.readHumidity();
  float testTemperature = dht.readTemperature();
  if (!isnan(testHumidity) && !isnan(testTemperature)) {
    dhtSensorConnected = true;
    Serial.println("[OK] DHT22 Sensor: CONNECTED");
  } else {
    dhtSensorConnected = false;
    Serial.println("[--] DHT22 Sensor: NOT CONNECTED");
  }

  // BH1750
  Wire.begin(I2C_SDA, I2C_SCL);
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    delay(200);
    float testLight = lightMeter.readLightLevel();
    if (testLight >= 0) {
      lightSensorConnected = true;
      Serial.println("[OK] BH1750 Light Sensor: CONNECTED");
    } else {
      lightSensorConnected = false;
      Serial.println("[--] BH1750 Light Sensor: NOT CONNECTED");
    }
  } else {
    lightSensorConnected = false;
    Serial.println("[--] BH1750 Light Sensor: NOT CONNECTED");
  }

  Serial.println("-------------------------\n");
}

// =============================================================================
// Re-detect Offline Sensors During Runtime
// =============================================================================
void redetectOfflineSensors() {
  unsigned long now = millis();
  if (now - lastRedetectTime < SENSOR_REDETECT_INTERVAL_MS) return;
  lastRedetectTime = now;

  if (!dhtSensorConnected) {
    dht.begin();
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(h) && !isnan(t)) {
      dhtSensorConnected = true;
      Serial.println("[OK] DHT22 Sensor: RECONNECTED");
    }
  }

  if (!lightSensorConnected) {
    if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
      delay(50);
      float lux = lightMeter.readLightLevel();
      if (lux >= 0) {
        lightSensorConnected = true;
        Serial.println("[OK] BH1750 Sensor: RECONNECTED");
      }
    }
  }
}

// =============================================================================
// Read Sensors
// =============================================================================
void readSensors() {
  // Soil Moisture
  if (soilSensorConnected) {
    int rawValue   = analogRead(SOIL_MOISTURE_PIN);
    int percentage = map(rawValue, SOIL_MOISTURE_DRY, SOIL_MOISTURE_WET, 0, 100);
    soilMoisture   = (float)constrain(percentage, 0, 100);
  } else {
    soilMoisture = NAN;
  }

  // DHT22: always attempt read (prevents getting stuck in OFFLINE after one failed detect)
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (!isnan(h) && !isnan(t)) {
    humidity    = h;
    temperature = t;
    dhtSensorConnected = true;
  } else {
    humidity    = NAN;
    temperature = NAN;
    dhtSensorConnected = false;
    Serial.println("WARNING: DHT22 read failed.");
  }

  // BH1750: always attempt read and recover automatically when sensor comes back
  float lux = lightMeter.readLightLevel();
  if (lux >= 0) {
    lightLevel = lux;
    lightSensorConnected = true;
  } else {
    lightLevel = NAN;
    lightSensorConnected = false;
    Serial.println("WARNING: BH1750 read failed.");
  }
}

// =============================================================================
// Print Sensor Status
// =============================================================================
void printSensorStatus() {
  Serial.println("--- Sensor Readings ---");

  Serial.print("Soil Moisture : ");
  Serial.println(!isnan(soilMoisture) ? String(soilMoisture) + "%" : "OFFLINE");

  Serial.print("Temperature   : ");
  Serial.println(!isnan(temperature) ? String(temperature) + "C" : "OFFLINE");

  Serial.print("Humidity      : ");
  Serial.println(!isnan(humidity) ? String(humidity) + "%" : "OFFLINE");

  Serial.print("Light Level   : ");
  Serial.println(!isnan(lightLevel) ? String(lightLevel) + " lux" : "OFFLINE");

  Serial.println("-----------------------");
}

// =============================================================================
// Float or Null (send null for disconnected sensors)
// =============================================================================
String floatOrNull(float value) {
  if (isnan(value)) return "null";
  return String(value, 2);
}

bool postSensorDataToBackendAtIndex(int endpointIndex, const String& jsonPayload) {
  HTTPClient http;
  String apiUrl = String(API_BASE_URLS[endpointIndex]) + "/sensors/" + deviceId + "/readings";
  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  int httpResponseCode = http.POST(jsonPayload);
  http.end();

  if (httpResponseCode > 0 && httpResponseCode < 300) {
    return true;
  }

  Serial.print("Sensor POST failed on ");
  Serial.print(API_BASE_URLS[endpointIndex]);
  Serial.print(" with code ");
  Serial.println(httpResponseCode);
  return false;
}

bool fetchControlStateFromBackendAtIndex(int endpointIndex) {
  HTTPClient http;
  String url = String(API_BASE_URLS[endpointIndex]) + "/irrigation/control/" + deviceId;
  http.begin(url);
  int httpResponseCode = http.GET();

  if (httpResponseCode != 200) {
    http.end();
    Serial.print("Control GET failed on ");
    Serial.print(API_BASE_URLS[endpointIndex]);
    Serial.print(" with code ");
    Serial.println(httpResponseCode);
    return false;
  }

  String payload = http.getString();
  http.end();

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.print("Control JSON parse failed on ");
    Serial.print(API_BASE_URLS[endpointIndex]);
    Serial.print(": ");
    Serial.println(error.c_str());
    return false;
  }

  bool pumpState = doc["pump_state"];

  Serial.print("Pump state from backend: ");
  Serial.println(pumpState ? "ON" : "OFF");

  setPumpState(pumpState);
  
  Serial.print("Relay signal sent: ");
  if (RELAY_ACTIVE_LOW) {
    Serial.println(pumpState ? "LOW (Pump ON)" : "HIGH (Pump OFF)");
  } else {
    Serial.println(pumpState ? "HIGH (Pump ON)" : "LOW (Pump OFF)");
  }

  return true;
}

// =============================================================================
// Send Data to Backend
// =============================================================================
void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WARNING: WiFi disconnected, skipping send.");
    return;
  }

  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\""   + deviceId              + "\",";
  jsonPayload += "\"soil_moisture\":" + floatOrNull(soilMoisture) + ",";
  jsonPayload += "\"temperature\":"   + floatOrNull(temperature)  + ",";
  jsonPayload += "\"humidity\":"      + floatOrNull(humidity)     + ",";
  jsonPayload += "\"light_level\":"   + floatOrNull(lightLevel);
  jsonPayload += "}";

  Serial.print("Sending: ");
  Serial.println(jsonPayload);

  for (int offset = 0; offset < API_BASE_URL_COUNT; offset++) {
    int endpointIndex = (activeApiIndex + offset) % API_BASE_URL_COUNT;
    if (postSensorDataToBackendAtIndex(endpointIndex, jsonPayload)) {
      if (endpointIndex != activeApiIndex) {
        Serial.print("Switched active API endpoint to: ");
        Serial.println(API_BASE_URLS[endpointIndex]);
      }
      activeApiIndex = endpointIndex;
      return;
    }
  }

  Serial.println("ERROR: Sensor data send failed on all configured API endpoints.");
}

// =============================================================================
// Poll Control State
// =============================================================================
void pollControlState() {
  if (WiFi.status() != WL_CONNECTED) return;

  for (int offset = 0; offset < API_BASE_URL_COUNT; offset++) {
    int endpointIndex = (activeApiIndex + offset) % API_BASE_URL_COUNT;
    if (fetchControlStateFromBackendAtIndex(endpointIndex)) {
      if (endpointIndex != activeApiIndex) {
        Serial.print("Switched active API endpoint to: ");
        Serial.println(API_BASE_URLS[endpointIndex]);
      }
      activeApiIndex = endpointIndex;
      return;
    }
  }

  Serial.println("ERROR: Control state fetch failed on all configured API endpoints.");
}

// =============================================================================
// Setup
// =============================================================================
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  setPumpState(false); // Always boot with pump OFF to avoid startup pulse

  delay(1000);
  Serial.println("=== AgriSense Starting ===");
  setupWifi();
  generateDeviceId();
  detectSensors();
}

// =============================================================================
// Loop
// =============================================================================
void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastReadTime >= SENSOR_READ_INTERVAL_MS) {
    lastReadTime = currentMillis;
    redetectOfflineSensors();
    readSensors();
    printSensorStatus();
    sendDataToBackend();
    pollControlState();
  }
}
