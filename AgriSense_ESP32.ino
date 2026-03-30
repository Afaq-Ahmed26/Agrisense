// =============================================================================
// AgriSense Smart Irrigation System (V4 - Auto Sensor Detection)
//
// Author: Afaq Ahmed
// Date: March 26, 2026
//
// Description:
// Automatically detects which sensors are connected.
// Connected sensors send real values, disconnected ones send null.
// No code changes needed when swapping sensors - just plug and play.
// =============================================================================

#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <BH1750.h>

// =============================================================================
// Pin Definitions
// =============================================================================
const int SOIL_MOISTURE_PIN = 34;
const int DHT_PIN            = 4;
const int I2C_SDA            = 21;  // BH1750 SDA
const int I2C_SCL            = 22;  // BH1750 SCL

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
const char* API_BASE_URL  = "http://192.168.100.253:8000";

// =============================================================================
// Calibration Values
// =============================================================================
const int SOIL_MOISTURE_DRY = 2950;
const int SOIL_MOISTURE_WET = 1250;

// =============================================================================
// Timing
// =============================================================================
const unsigned long SENSOR_READ_INTERVAL_MS = 10000;
unsigned long lastReadTime = 0;

// =============================================================================
// Sensor State Flags (auto-detected at startup)
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
  // Hardcoded for development consistency with frontend/mock-backend
  deviceId = "esp32-b47cb8";
  Serial.print("Device ID (Fixed): ");
  Serial.println(deviceId);
}

// =============================================================================
// Auto-Detect Sensors at Startup
// =============================================================================
void detectSensors() {
  Serial.println("\n--- Detecting Sensors ---");

  // --- Soil Moisture ---
  // Read a few times to check if it gives a valid analog range
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  // If pin is floating it usually reads 0 or 4095 consistently
  // A connected sensor reads somewhere in between
  if (rawValue > 100 && rawValue < 4000) {
    soilSensorConnected = true;
    Serial.println("✅ Soil Moisture Sensor: CONNECTED");
  } else {
    soilSensorConnected = false;
    Serial.println("❌ Soil Moisture Sensor: NOT CONNECTED");
  }

  // --- DHT22 ---
  dht.begin();
  delay(2000); // DHT22 needs 2 seconds after power-on
  float testHumidity    = dht.readHumidity();
  float testTemperature = dht.readTemperature();
  if (!isnan(testHumidity) && !isnan(testTemperature)) {
    dhtSensorConnected = true;
    Serial.println("✅ DHT22 Sensor: CONNECTED");
  } else {
    dhtSensorConnected = false;
    Serial.println("❌ DHT22 Sensor: NOT CONNECTED");
  }

  // --- BH1750 Light Sensor ---
  Wire.begin(I2C_SDA, I2C_SCL);
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    // Try reading to confirm it's actually there
    delay(200);
    float testLight = lightMeter.readLightLevel();
    if (testLight >= 0) {
      lightSensorConnected = true;
      Serial.println("✅ BH1750 Light Sensor: CONNECTED");
    } else {
      lightSensorConnected = false;
      Serial.println("❌ BH1750 Light Sensor: NOT CONNECTED");
    }
  } else {
    lightSensorConnected = false;
    Serial.println("❌ BH1750 Light Sensor: NOT CONNECTED");
  }

  Serial.println("-------------------------\n");
}

// =============================================================================
// Read Sensors (only reads connected ones)
// =============================================================================
void readSensors() {
  // --- Soil Moisture ---
  if (soilSensorConnected) {
    int rawValue   = analogRead(SOIL_MOISTURE_PIN);
    int percentage = map(rawValue, SOIL_MOISTURE_DRY, SOIL_MOISTURE_WET, 0, 100);
    soilMoisture   = (float)constrain(percentage, 0, 100);
  } else {
    soilMoisture = NAN;
  }

  // --- DHT22 ---
  if (dhtSensorConnected) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    // Re-check in case sensor disconnected after startup
    if (!isnan(h) && !isnan(t)) {
      humidity    = h;
      temperature = t;
    } else {
      humidity    = NAN;
      temperature = NAN;
      Serial.println("⚠️  DHT22 lost connection!");
    }
  } else {
    humidity    = NAN;
    temperature = NAN;
  }

  // --- BH1750 ---
  if (lightSensorConnected) {
    float lux = lightMeter.readLightLevel();
    if (lux >= 0) {
      lightLevel = lux;
    } else {
      lightLevel = NAN;
      Serial.println("⚠️  BH1750 lost connection!");
    }
  } else {
    lightLevel = NAN;
  }
}

// =============================================================================
// Print Sensor Status to Serial Monitor
// =============================================================================
void printSensorStatus() {
  Serial.println("--- Sensor Readings ---");

  if (!isnan(soilMoisture)) {
    Serial.print("🌱 Soil Moisture : "); Serial.print(soilMoisture); Serial.println("%");
  } else {
    Serial.println("🌱 Soil Moisture : OFFLINE");
  }

  if (!isnan(temperature)) {
    Serial.print("🌡️  Temperature   : "); Serial.print(temperature); Serial.println("°C");
  } else {
    Serial.println("🌡️  Temperature   : OFFLINE");
  }

  if (!isnan(humidity)) {
    Serial.print("💧 Humidity      : "); Serial.print(humidity); Serial.println("%");
  } else {
    Serial.println("💧 Humidity      : OFFLINE");
  }

  if (!isnan(lightLevel)) {
    Serial.print("☀️  Light Level   : "); Serial.print(lightLevel); Serial.println(" lux");
  } else {
    Serial.println("☀️  Light Level   : OFFLINE");
  }

  Serial.println("-----------------------");
}

// =============================================================================
// Build JSON value helper
// =============================================================================
String floatOrNull(float value) {
  if (isnan(value)) return "null";
  return String(value, 2); // 2 decimal places
}

// =============================================================================
// Send Data to Backend
// =============================================================================
void sendDataToBackend() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️  WiFi disconnected, skipping send.");
    return;
  }

  HTTPClient http;
  String apiUrl = String(API_BASE_URL) + "/sensors/" + deviceId + "/readings";

  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\""  + deviceId          + "\",";
  jsonPayload += "\"soil_moisture\":" + floatOrNull(soilMoisture) + ",";
  jsonPayload += "\"temperature\":"   + floatOrNull(temperature)  + ",";
  jsonPayload += "\"humidity\":"      + floatOrNull(humidity)     + ",";
  jsonPayload += "\"light_level\":"   + floatOrNull(lightLevel);
  jsonPayload += "}";

  Serial.print("📤 Sending: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);
  Serial.print("📥 Response: ");
  Serial.println(httpResponseCode);
  http.end();
}

// =============================================================================
// Setup
// =============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== AgriSense V4 Starting ===");
  setupWifi();
  generateDeviceId();
  detectSensors(); // Auto-detect once at startup
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
  }
}