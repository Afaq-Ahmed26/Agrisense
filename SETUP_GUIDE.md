# AgriSense - Real Hardware Setup Guide

## ✅ What's Already Done

1. **Backend Server**: Running at `http://192.168.100.253:8000`
2. **Firebase Admin SDK**: Configured with service account
3. **Test User Created**: 
   - Email: `test@agrisense.com`
   - Password: `test123`
4. **Test Device Created**: 
   - Device ID: `device_ba15671065d89b2a`

---

## 📋 Step 1: Upload Code to ESP32

### Wiring Connections
```
Soil Moisture Sensor:
  VCC  → ESP32 3V3 (or VIN)
  GND  → ESP32 GND
  AOUT → ESP32 GPIO 34
```

### Arduino IDE Setup
1. Open `AgriSense_ESP32.ino` in Arduino IDE
2. Install required libraries:
   - Board: ESP32 (by Espressif Systems)
   - No additional libraries needed for soil moisture only!
3. Update WiFi credentials in code (already set):
   ```cpp
   const char* WIFI_SSID = "Agrisense";
   const char* WIFI_PASSWORD = "passwordd";
   ```
4. Update API URL (already set):
   ```cpp
   const char* API_BASE_URL = "http://192.168.100.253:8000";
   ```
5. Device ID (already set):
   ```cpp
   deviceId = "device_ba15671065d89b2a";
   ```
6. Select your ESP32 board and port
7. Click Upload

### Expected Serial Monitor Output (115200 baud)
```
========================================
AgriSense - Soil Moisture Sensor Test
========================================
Connecting to WiFi....
WiFi Connected!
IP Address: 192.168.100.xxx
Device ID: device_ba15671065d89b2a
Setup complete. Starting sensor readings...

=== AgriSense - Soil Moisture Test ===
Soil Moisture: XX%
Sending to backend: {"device_id":"device_ba15671065d89b2a",...}
HTTP Response Code: 200
SUCCESS: Data sent to backend!
```

---

## 🔧 Step 2: Configure Firebase Web (for Frontend)

### Get Firebase Web Config
1. Go to https://console.firebase.google.com/project/agrisense-ue/settings/general
2. Scroll to "Your apps"
3. Click Web icon (</>)
4. Register app if needed
5. Copy the `firebaseConfig` object

### Update Frontend .env
Edit `Frontend/.env`:
```env
# Replace with YOUR actual Firebase web config
VITE_FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX
VITE_FIREBASE_AUTH_DOMAIN=agrisense-ue.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=agrisense-ue
VITE_FIREBASE_STORAGE_BUCKET=agrisense-ue.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123def456

# Backend API URL
VITE_API_BASE_URL=http://192.168.100.253:8000
```

### Restart Frontend
```bash
cd Frontend
npm run dev
```

---

## 🌐 Step 3: Test Frontend

1. Open browser: `http://localhost:5173`
2. Login with:
   - Email: `test@agrisense.com`
   - Password: `test123`
3. Navigate to Dashboard
4. You should see:
   - Soil Moisture card with live value
   - Temperature: 0% (not connected yet)
   - Humidity: 0% (not connected yet)
   - Light Level: 0 lx (not connected yet)

---

## 🔍 Troubleshooting

### ESP32 shows "HTTP Response Code: -1" or "Connection failed"
- Check WiFi credentials
- Ensure ESP32 and computer are on same network
- Check firewall allows port 8000
- Verify API_BASE_URL is correct

### ESP32 shows "HTTP Response Code: 404"
- Check device ID matches the one in Firebase
- Verify endpoint is `/sensors/{device_id}/readings`

### Frontend shows "No sensor readings"
- Check backend is running: `curl http://192.168.100.253:8000/health`
- Check Firebase config in frontend .env
- Check browser console for errors

### Backend errors
- Check backend logs
- Verify Firebase credentials are valid
- Check `.env` file exists in `backend/` directory

---

## 📊 Data Flow

```
Soil Moisture Sensor
       ↓
   ESP32 (GPIO 34)
       ↓ (HTTP POST every 5 seconds)
   FastAPI Backend
       ↓ (Firestore SDK)
   Firebase Firestore
       ↓ (Real-time sync)
   Frontend Dashboard
```

---

## 📝 Collections in Firebase

### Firestore Collections:
- `devices` - Device metadata
  - `device_ba15671065d89b2a`
  
- `sensor_readings` - All sensor data
  - Each reading has: device_id, soil_moisture, temperature, humidity, light_level, timestamp

---

## ✅ Test Checklist

- [ ] ESP32 uploads successfully
- [ ] Serial Monitor shows "SUCCESS: Data sent to backend!"
- [ ] Backend logs show incoming requests
- [ ] Firebase Console shows data in `sensor_readings` collection
- [ ] Frontend displays soil moisture value
- [ ] Value updates every 5 seconds

---

## 🚀 Next Steps (After Soil Moisture Works)

1. **Add DHT22** - Uncomment DHT22 code for temperature & humidity
2. **Add BH1750** - Add I2C light sensor on GPIO 21/22
3. **Test ML Prediction** - Enable ML service for irrigation recommendations
