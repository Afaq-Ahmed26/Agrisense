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
const char* API_BASE_URL  = "http://192.168.100.13:8000";

// =============================================================================
// Calibration Values
// =============================================================================
const int SOIL_MOISTURE_DRY = 2950;
const int SOIL_MOISTURE_WET = 1250;

// =============================================================================
// Timing
// =============================================================================
const unsigned long SENSOR_READ_INTERVAL_MS = 2000;
unsigned long lastReadTime = 0;

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

  // DHT22
  if (dhtSensorConnected) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(h) && !isnan(t)) {
      humidity    = h;
      temperature = t;
    } else {
      humidity    = NAN;
      temperature = NAN;
      Serial.println("WARNING: DHT22 lost connection!");
    }
  } else {
    humidity    = NAN;
    temperature = NAN;
  }

  // BH1750
  if (lightSensorConnected) {
    float lux = lightMeter.readLightLevel();
    if (lux >= 0) {
      lightLevel = lux;
    } else {
      lightLevel = NAN;
      Serial.println("WARNING: BH1750 lost connection!");
    }
  } else {
    lightLevel = NAN;
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
// Float or Default (backend requires non-null values)
// =============================================================================
String floatOrDefault(float value, float defaultVal) {
  if (isnan(value)) return String(defaultVal, 2);
  return String(value, 2);
}

// =============================================================================
// Send Data to Backend
// =============================================================================
void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WARNING: WiFi disconnected, skipping send.");
    return;
  }

  HTTPClient http;
  String apiUrl = String(API_BASE_URL) + "/sensors/" + deviceId + "/readings";

  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\""   + deviceId                           + "\",";
  jsonPayload += "\"soil_moisture\":" + floatOrDefault(soilMoisture, 0.0)  + ",";
  jsonPayload += "\"temperature\":"   + floatOrDefault(temperature,  25.0) + ",";
  jsonPayload += "\"humidity\":"      + floatOrDefault(humidity,     50.0) + ",";
  jsonPayload += "\"light_level\":"   + floatOrDefault(lightLevel,   300.0);
  jsonPayload += "}";

  Serial.print("Sending: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);
  Serial.print("Response: ");
  Serial.println(httpResponseCode);
  http.end();
}

// =============================================================================
// Poll Control State
// =============================================================================
void pollControlState() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = String(API_BASE_URL) + "/irrigation/control/" + deviceId;
  http.begin(url);
  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String payload = http.getString();
    JsonDocument doc;
    deserializeJson(doc, payload);
    bool pumpState = doc["pump_state"];
    Serial.print("Backend pump_state: ");
    Serial.println(pumpState ? "ON" : "OFF");
    
    // Debugging print for the actual signal being sent
    Serial.print("Sending signal to RELAY_PIN (GPIO");
    Serial.print(RELAY_PIN);
    Serial.print("): ");
    Serial.println(pumpState ? "LOW (Active-Low ON)" : "HIGH (Active-Low OFF)");

    // Invert HIGH/LOW to test for active-low relay
    digitalWrite(RELAY_PIN, pumpState ? LOW : HIGH);
  } else {
    Serial.print("Failed to get control state. HTTP Response code: ");
    Serial.println(httpResponseCode);
  }
  http.end();
}

// =============================================================================
// Setup
// =============================================================================
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // Initialize to OFF (Active-Low)
  delay(1000);
  Serial.println("\n=== AgriSense Starting ===");
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
    readSensors();
    printSensorStatus();
    sendDataToBackend();
    pollControlState();
  }
}
