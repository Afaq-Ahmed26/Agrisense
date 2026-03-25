// =============================================================================
// AgriSense Smart Irrigation System (V2 - Networked)
//
// Author: Afaq Ahmed
// Date: March 1, 2026
//
// Description:
// This code runs on an ESP32 microcontroller to automate a simple irrigation
// system. It reads data from sensors and sends it to a backend API over Wi-Fi.
// It also controls a solenoid valve based on soil moisture thresholds.
//
// Hardware:
// - ESP32 Dev Module
// - Capacitive Soil Moisture Sensor (Analog) -> GPIO 34
// - DHT22 Temperature & Humidity Sensor -> GPIO 4
// - LDR (Light Dependent Resistor) -> GPIO 35
// - 5V Relay Module -> GPIO 26
// - 12V DC Solenoid Valve
// =============================================================================

// =============================================================================
// Section 1: Libraries
// =============================================================================
// =============================================================================
// AgriSense Smart Irrigation System - SOIL MOISTURE ONLY TEST
// =============================================================================
// FOCUS: Testing soil moisture sensor integration only (GPIO 34)
// All other sensors (DHT22, LDR/BH1750) and relay control are commented out
// to isolate and debug the soil moisture data flow: ESP32 → Backend → Firebase → Frontend
// =============================================================================

#include <Arduino.h>
// #include <DHT.h>  // COMMENTED OUT: DHT22 temperature/humidity sensor - not testing today
#include <WiFi.h>
#include <HTTPClient.h>

// =============================================================================
// Pin Definitions
// =============================================================================
const int SOIL_MOISTURE_PIN = 34;  // Soil moisture sensor analog output
// COMMENTED OUT BELOW - Not testing today:
// const int DHT_PIN = 4;           // DHT22 temperature & humidity sensor
// const int LDR_PIN = 35;          // LDR light sensor (we tested BH1750 on I2C instead)
// const int RELAY_PIN = 26;        // Relay control for solenoid valve

// =============================================================================
// DHT Setup - COMMENTED OUT
// =============================================================================
// #define DHTTYPE DHT22
// DHT dht(DHT_PIN, DHTTYPE);
// Purpose: Read temperature and humidity from DHT22 sensor
// Not testing today - focusing on soil moisture only

// =============================================================================
// Network Configuration (EDIT THESE)
// =============================================================================
const char* WIFI_SSID = "Agrisense";
const char* WIFI_PASSWORD = "passwordd";
// Updated: Backend server IP address (your computer's current IP)
const char* API_BASE_URL = "http://192.168.43.120:8000";

// =============================================================================
// Calibration Values
// =============================================================================
// These values are from your sensor test:
// - DRY (in air): 2500-3200
// - WET (in water): 800-1500
const int SOIL_MOISTURE_DRY = 2950;  // Raw ADC value when sensor is dry
const int SOIL_MOISTURE_WET = 1250;  // Raw ADC value when sensor is wet

// COMMENTED OUT - Control thresholds for automatic irrigation (not testing today)
// const int MOISTURE_TURN_ON_THRESHOLD = 40;   // Turn on when moisture < 40%
// const int MOISTURE_TURN_OFF_THRESHOLD = 60;  // Turn off when moisture >= 60%

// Sensor reading interval - FAST for demo purposes
// Change to 5000-10000 for production use
const unsigned long SENSOR_READ_INTERVAL_MS = 2000;  // 2000ms = 2 seconds (DEMO MODE)
unsigned long lastReadTime = 0;

// =============================================================================
// Global Variables
// =============================================================================
float soilMoisture = 0.0;  // Soil moisture percentage (0-100%)
// COMMENTED OUT - Not testing today:
// float temperature = 0.0;    // DHT22 temperature in Celsius
// float humidity = 0.0;       // DHT22 humidity percentage
// int lightLevel = 0;         // Light level percentage (LDR or BH1750)
// bool isRelayOn = false;     // Relay/solenoid valve status
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
  uint64_t chipid = ESP.getEfuseMac();
  deviceId = "esp32-" + String((uint32_t)(chipid >> 24), HEX);
  Serial.print("Device ID: ");
  Serial.println(deviceId);
}

// =============================================================================
// Sensor Functions
// =============================================================================

// Read soil moisture sensor and convert to percentage (0-100%)
float readSoilMoisture() {
  int rawValue = analogRead(SOIL_MOISTURE_PIN);
  int percentage = map(rawValue, SOIL_MOISTURE_DRY, SOIL_MOISTURE_WET, 0, 100);
  return constrain(percentage, 0, 100);
}

// COMMENTED OUT - DHT22 sensor reading function
// Purpose: Read temperature and humidity from DHT22 sensor
// Not testing today - focusing on soil moisture only
/*
void readDHTSensor() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (!isnan(h) && !isnan(t)) {
    humidity = h;
    temperature = t;
  } else {
    Serial.println("Failed to read DHT sensor!");
  }
}
*/

// COMMENTED OUT - LDR light sensor reading function
// Purpose: Read light level using LDR (Light Dependent Resistor) on GPIO 35
// Note: We tested BH1750 on I2C (GPIO 21/22) instead - will add that later
/*
int readLightLevel() {
  int rawValue = analogRead(LDR_PIN);
  int percentage = map(rawValue, 0, 4095, 100, 0);
  return constrain(percentage, 0, 100);
}
*/

// =============================================================================
// Control Logic - COMMENTED OUT
// =============================================================================
// Purpose: Automatically control solenoid valve based on soil moisture thresholds
// - Turn ON irrigation when soil moisture < 40%
// - Turn OFF irrigation when soil moisture >= 60%
// Not testing today - focusing on sensor data display only
/*
void controlSolenoid() {
  if (soilMoisture < MOISTURE_TURN_ON_THRESHOLD && !isRelayOn) {
    digitalWrite(RELAY_PIN, HIGH);
    isRelayOn = true;
  }
  else if (soilMoisture >= MOISTURE_TURN_OFF_THRESHOLD && isRelayOn) {
    digitalWrite(RELAY_PIN, LOW);
    isRelayOn = false;
  }
}
*/

// =============================================================================
// Print System Status - SOIL MOISTURE ONLY
// =============================================================================
// Purpose: Display sensor readings on Serial Monitor for debugging
void printReadings() {
  Serial.println("\n=== AgriSense - Soil Moisture Test ===");
  Serial.print("Soil Moisture: ");
  Serial.print(soilMoisture);
  Serial.println("%");

  // COMMENTED OUT - Not testing today:
  /*
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println("%");

  Serial.print("Light Level: ");
  Serial.print(lightLevel);
  Serial.println("%");

  Serial.print("Relay: ");
  Serial.println(isRelayOn ? "ON" : "OFF");
  */
}

// =============================================================================
// Send Data to Backend - SOIL MOISTURE ONLY
// =============================================================================
// Purpose: Send soil moisture sensor reading to FastAPI backend
// Backend endpoint: POST /sensors/{device_id}/readings
// Data is then stored in Firebase Firestore
void sendDataToBackend() {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected.");
    return;
  }

  HTTPClient http;

  // Build API URL with device ID
  // Note: Endpoint is /sensors/{device_id}/readings (not /api/sensors/...)
  String apiUrl = String(API_BASE_URL) + "/sensors/" + deviceId + "/readings";

  http.begin(apiUrl);
  http.addHeader("Content-Type", "application/json");

  // Build JSON payload - SOIL MOISTURE ONLY
  // Backend expects: device_id, soil_moisture, temperature, humidity, light_level
  // We'll send dummy values (0) for sensors we're not testing
  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\"" + deviceId + "\",";
  jsonPayload += "\"soil_moisture\":" + String(soilMoisture) + ",";
  jsonPayload += "\"temperature\":0,";      // Dummy value - not testing DHT22 today
  jsonPayload += "\"humidity\":0,";         // Dummy value - not testing DHT22 today
  jsonPayload += "\"light_level\":0";       // Dummy value - not testing light sensor today
  jsonPayload += "}";

  Serial.print("Sending to backend: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  Serial.print("HTTP Response Code: ");
  Serial.println(httpResponseCode);

  if (httpResponseCode > 0) {
    if (httpResponseCode == 200) {
      Serial.println("SUCCESS: Data sent to backend!");
    } else {
      Serial.print("WARNING: Backend returned error code: ");
      Serial.println(httpResponseCode);
    }
  } else {
    Serial.print("ERROR: HTTP POST failed: ");
    Serial.println(http.errorToString(httpResponseCode));
  }

  http.end();
}

// =============================================================================
// Setup
// =============================================================================
void setup() {

  Serial.begin(115200);
  Serial.println("\n========================================");
  Serial.println("AgriSense - Soil Moisture Sensor Test");
  Serial.println("========================================");

  // COMMENTED OUT - Relay pin setup (not testing irrigation control today)
  /*
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Ensure relay is OFF at startup
  */

  // COMMENTED OUT - DHT sensor initialization (not testing today)
  // dht.begin();

  // Connect to WiFi
  setupWifi();
  
  // Generate unique device ID
  generateDeviceId();
  
  Serial.println("Setup complete. Starting sensor readings...");
  Serial.println();
}

// =============================================================================
// Main Loop
// =============================================================================
void loop() {

  unsigned long currentMillis = millis();

  // Read sensors and send data every SENSOR_READ_INTERVAL_MS (5 seconds)
  if (currentMillis - lastReadTime >= SENSOR_READ_INTERVAL_MS) {
    lastReadTime = currentMillis;

    // Read soil moisture sensor
    soilMoisture = readSoilMoisture();
    
    // COMMENTED OUT - Not testing today:
    // readDHTSensor();
    // lightLevel = readLightLevel();

    // COMMENTED OUT - Automatic irrigation control (not testing today)
    // controlSolenoid();
    
    // Display readings on Serial Monitor
    printReadings();
    
    // Send data to backend API
    sendDataToBackend();
    
    Serial.println("\n--- Waiting for next reading ---\n");
  }
}
