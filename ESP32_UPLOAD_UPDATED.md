# 📡 ESP32 Upload Instructions - UPDATED

## ⚠️ NETWORK CHANGED - IP Updated!

| Item | Old Value | **NEW Value** |
|------|-----------|---------------|
| **Computer IP** | 192.168.100.253 | **192.168.43.120** |
| **Backend URL** | http://192.168.100.253:8000 | **http://192.168.43.120:8000** |
| **WiFi Name** | Agrisense | Agrisense (same) |
| **WiFi Password** | passwordd | passwordd (same) |

---

## ✅ Code Ready to Upload

**File:** `AgriSense_ESP32.ino`

### Configuration (Already Updated)
```cpp
const char* WIFI_SSID = "Agrisense";
const char* WIFI_PASSWORD = "passwordd";
const char* API_BASE_URL = "http://192.168.43.120:8000";  // ← UPDATED!
deviceId = "device_ba15671065d89b2a";
```

### Wiring (Same as Before)
```
Soil Moisture Sensor:
  VCC  → ESP32 3V3
  GND  → ESP32 GND
  AOUT → ESP32 GPIO 34
```

---

## 🚀 Upload Steps

1. **Open Arduino IDE**
2. **Open** `AgriSense_ESP32.ino`
3. **Select Board:** ESP32 Dev Module (or your board)
4. **Select Port:** (e.g., /dev/ttyUSB0 or COM3)
5. **Click Upload** (→ arrow button)
6. **Open Serial Monitor** (115200 baud)

---

## 📺 Expected Serial Monitor Output

```
========================================
AgriSense - Soil Moisture Sensor Test
========================================
Connecting to WiFi....
WiFi Connected!
IP Address: 192.168.43.xxx
Device ID: device_ba15671065d89b2a
Setup complete. Starting sensor readings...

=== AgriSense - Soil Moisture Test ===
Soil Moisture: 45%
Sending to backend: {"device_id":"device_ba15671065d89b2a",...}
HTTP Response Code: 200
SUCCESS: Data sent to backend!

--- Waiting for next reading ---
```

---

## ✅ Success Checklist

- [ ] WiFi credentials correct (Agrisense / passwordd)
- [ ] Backend IP updated to `192.168.43.120`
- [ ] Device ID is `device_ba15671065d89b2a`
- [ ] Code uploads without errors
- [ ] Serial shows "WiFi Connected!"
- [ ] Serial shows "HTTP Response Code: 200"
- [ ] Serial shows "SUCCESS: Data sent to backend!"

---

## 🔍 Troubleshooting

### "Connecting to WiFi..." forever
- Check WiFi name is correct: `Agrisense`
- Check password is correct: `passwordd`
- Ensure ESP32 is in range of WiFi

### "HTTP Response Code: -1" or "Connection failed"
- Check backend is running: `curl http://192.168.43.120:8000/health`
- Ensure ESP32 and computer on same network
- Check firewall allows port 8000

### "HTTP Response Code: 404"
- Device ID is wrong
- Use: `device_ba15671065d89b2a`

### Backend Not Running
```bash
cd /home/afaq-ahmed/Desktop/Agriscense/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Test Backend is Running

```bash
curl http://192.168.43.120:8000/health
```

Expected: `{"status":"healthy","service":"agrisense-backend"}`

---

## 📊 Test with Curl (Simulate ESP32)

```bash
curl -X POST http://192.168.43.120:8000/sensors/device_ba15671065d89b2a/readings \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device_ba15671065d89b2a","soil_moisture":45,"temperature":0,"humidity":0,"light_level":0}'
```

Expected: Success with reading ID and timestamp

---

## 🎯 What's Active in Code

✅ **Active:**
- Soil Moisture Sensor (GPIO 34)
- WiFi Connection
- HTTP POST to backend every 5 seconds

❌ **Commented Out (Not Testing):**
- DHT22 Temperature/Humidity
- Light Sensor (LDR/BH1750)
- Relay Control
- Automatic Irrigation
- ML Prediction

---

**Upload the code and share Serial Monitor output!**
