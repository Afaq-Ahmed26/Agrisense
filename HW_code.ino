#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"  // Include the DHT sensor library
#include <Wire.h>  // Include Wire library for I2C communication
#include <BH1750.h>  // Include BH1750 library

#define DHT_PIN 15         // GPIO pin where DHT22 is connected
#define DHT_TYPE DHT22     // DHT 22 (AM2302), AM2321

// Initialize DHT sensor
DHT dht(DHT_PIN, DHT_TYPE);

// Initialize BH1750 sensor
BH1750 lightMeter;

// Relay pin definition
const int RELAY_PIN = 2;  // GPIO pin where relay is connected

const int SOIL_MOISTURE_PIN = 34;

const char* WIFI_SSID     = "Agrisense";
const char* WIFI_PASSWORD = "passwordd";
const char* API_BASE_URL  = "http://192.168.43.120:8000";

// ⚠️ We will update these after seeing raw values
const int SOIL_MOISTURE_DRY = 2950;
const int SOIL_MOISTURE_WET = 1250;

const unsigned long SENSOR_READ_INTERVAL_MS = 10000;
unsigned long lastReadTime = 0;

float soilMoisture = 0.0;
float temperature = 0.0;
float humidity = 0.0;
float lightLevel = 0.0;
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

// Function to read temperature and humidity from DHT22
bool readDHT22() {
  // Allow the DHT22 some time to settle before reading
  delay(250);

  // Read humidity and temperature from DHT22
  float newHumidity = dht.readHumidity();
  float newTemperature = dht.readTemperature(); // Celsius by default

  // Check if any reads failed and exit early (to try again).
  if (isnan(newHumidity) || isnan(newTemperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return false;
  }

  // Update global variables
  humidity = newHumidity;
  temperature = newTemperature;

  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C, Humidity: ");
  Serial.print(humidity);
  Serial.println("%");

  return true;
}

// =============================================================================
// BH1750 Light Sensor Functions
// =============================================================================
bool readBH1750() {
  // Read light level from BH1750
  float lux = lightMeter.readLightLevel();

  if (isnan(lux)) {
    Serial.println("Failed to read from BH1750 sensor!");
    return false;
  }

  // Update global variable
  lightLevel = lux;

  Serial.print("Light Level: ");
  Serial.print(lightLevel);
  Serial.println(" lx");

  return true;
}

// =============================================================================
// Relay Control Functions
// =============================================================================
void setupRelay() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // Start with relay OFF (solenoid closed)
  Serial.println("Relay initialized and set to OFF");
}

void controlRelay(bool state) {
  if(state) {
    digitalWrite(RELAY_PIN, HIGH);  // Turn ON relay (solenoid open)
    Serial.println("Relay turned ON - Solenoid valve OPEN");
  } else {
    digitalWrite(RELAY_PIN, LOW);   // Turn OFF relay (solenoid closed)
    Serial.println("Relay turned OFF - Solenoid valve CLOSED");
  }
}

void printReadings() {
  Serial.println("\n--- AgriSense Status ---");
  Serial.print("Soil Moisture: ");
  Serial.print(soilMoisture);
  Serial.println("%");
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C, Humidity: ");
  Serial.print(humidity);
  Serial.println("%");
  Serial.print("Light Level: ");
  Serial.print(lightLevel);
  Serial.println(" lx");
  Serial.print("Relay State: ");
  Serial.println(digitalRead(RELAY_PIN) ? "ON" : "OFF");
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

  // Updated JSON payload with real sensor values
  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\""   + deviceId + "\",";
  jsonPayload += "\"soil_moisture\":" + String(soilMoisture, 2) + ",";
  jsonPayload += "\"temperature\":"   + String(temperature, 2) + ",";  // Updated to real value
  jsonPayload += "\"humidity\":"      + String(humidity, 2) + ",";     // Updated to real value
  jsonPayload += "\"light_level\":"   + String(lightLevel, 2);         // Updated to real value
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

  // Initialize DHT sensor
  dht.begin();

  // Initialize BH1750 sensor
  if (lightMeter.begin()) {
    Serial.println("BH1750 sensor initialized successfully!");
  } else {
    Serial.println("Error: Unable to initialize BH1750 sensor!");
  }

  // Initialize relay
  setupRelay();

  generateDeviceId();
  setupWifi();
}

void loop() {
  unsigned long currentTime = millis();
  if (currentTime - lastReadTime >= SENSOR_READ_INTERVAL_MS) {
    lastReadTime = currentTime;

    // Read all sensors
    soilMoisture = readSoilMoisture();
    bool dhtSuccess = readDHT22();
    bool bh1750Success = readBH1750();

    if(dhtSuccess && bh1750Success) {
      // Basic irrigation logic: if soil moisture is below threshold, turn on relay
      const float MOISTURE_THRESHOLD = 30.0; // Turn on irrigation if soil moisture is below 30%

      if(soilMoisture < MOISTURE_THRESHOLD) {
        controlRelay(true);  // Turn ON irrigation
      } else {
        controlRelay(false); // Turn OFF irrigation
      }

      printReadings();
      sendDataToBackend();
    } else {
      if(!dhtSuccess) {
        Serial.println("Skipping data send due to DHT read failure");
      }
      if(!bh1750Success) {
        Serial.println("Skipping data send due to BH1750 read failure");
      }
    }
  }
}