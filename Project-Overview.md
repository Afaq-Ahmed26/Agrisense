# AgriSense - Smart Irrigation System
## Production-Ready Project Requirements

---

## 📌 Project Overview

**AgriSense** is a production-ready cloud + IoT + ML smart irrigation system that combines hardware sensors, machine learning predictions, and real-time web controls to optimize agricultural water usage.

### Core Value Proposition
- Automated irrigation based on real-time sensor data and ML predictions
- Remote monitoring and control via web dashboard
- Multi-user role system (Farmer, Middleman, Admin)
- Critical alerts for system failures and irrigation needs

---

## 🏗️ System Architecture

### Technology Stack
```
Hardware:     ESP32 + Soil Moisture + Temperature + Humidity Sensors + Relay Module + Solenoid Valves
ML Model:     Random Forest Regression (Python/scikit-learn)
Backend:      FastAPI (Python)
Database:     Firebase (Firestore + Realtime Database)
Frontend:     HTML + CSS + JavaScript
Communication: HTTPS, WebSockets, MQTT
```

### Data Flow Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Sensors   │ --> │    ESP32     │ --> │   Firebase  │ --> │  FastAPI     │
│ (Moisture,  │     │   (Process   │     │   (Cloud    │     │  (Backend    │
│  Temp,      │     │    & Send)   │     │   Storage)  │     │   API)       │
│  Humidity)  │     │              │     │             │     │              │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
                           ^                                         |
                           |                                         v
                    ┌──────────────┐                          ┌──────────────┐
                    │ Relay Module │ <----------------------- │  ML Model    │
                    │   (Control)  │                          │ (Prediction) │
                    └──────────────┘                          └──────────────┘
                           |                                         |
                           v                                         v
                    ┌──────────────┐                          ┌──────────────┐
                    │   Solenoid   │                          │     Web      │
                    │    Valves    │                          │  Dashboard   │
                    └──────────────┘                          └──────────────┘
```

---

## 🔧 Hardware Layer - ESP32 Firmware

### Hardware Components
- **Microcontroller**: ESP32 (WiFi-enabled)
- **Sensors**:
  - Soil Moisture Sensor (Capacitive/Resistive)
  - DHT22 or similar (Temperature + Humidity)
- **Actuators**:
  - Relay Module (5V, 1-4 channel)
  - Solenoid Valves (12V DC recommended)
- **Power**: 12V power supply with voltage regulator for ESP32

### Firmware Requirements

#### Core Functionality
1. **Sensor Data Collection**
   - Read soil moisture sensor (analog/digital)
   - Read temperature and humidity from DHT sensor
   - Sample rate: Every 30-60 seconds (configurable)
   - Data smoothing: Moving average filter to reduce noise

2. **Cloud Communication**
   - Connect to WiFi on startup
   - Send sensor data to Firebase Realtime Database
   - Listen for irrigation commands from Firebase
   - Implement reconnection logic with exponential backoff
   - Use HTTPS for secure communication

3. **Relay Control**
   - Control relay module to open/close solenoid valves
   - Support both automatic (from ML model) and manual (from dashboard) modes
   - Implement safety timeouts (max irrigation duration)
   - Emergency shutoff on sensor failure

4. **Safety Features**
   - **Failsafe Logic**: Auto-shutoff if sensors return invalid readings
   - **Watchdog Timer**: Reset ESP32 if system hangs
   - **Manual Override Timeout**: Auto-stop after configured duration (e.g., 30 minutes)
   - **Sensor Health Check**: Detect disconnected/broken sensors

5. **Power Management**
   - Deep sleep mode between sensor readings (optional for battery operation)
   - Wake on timer or external interrupt

6. **OTA Updates**
   - Over-The-Air firmware update capability
   - Version tracking and rollback support

### Expected Code Structure
```cpp
// main.ino
- WiFi connection management
- Firebase initialization
- Sensor reading functions
- Relay control functions
- Safety checks and error handling
- Loop with non-blocking delays

// config.h
- WiFi credentials
- Firebase project credentials
- Pin definitions
- Sensor thresholds
- Safety parameters
```

### Firebase Data Structure (ESP32 Side)
```json
{
  "devices": {
    "device_001": {
      "sensors": {
        "moisture": 45.2,
        "temperature": 28.5,
        "humidity": 65.3,
        "timestamp": 1704067200
      },
      "status": {
        "valve_open": false,
        "mode": "auto",
        "last_seen": 1704067200,
        "health": "ok"
      },
      "commands": {
        "irrigation_command": "stop",
        "duration": 0
      }
    }
  }
}
```

---

## 🤖 Machine Learning Layer

### Model Specifications

#### Algorithm
**Random Forest Regression**
- Proven reliability for agricultural predictions
- Handles non-linear relationships
- Resistant to overfitting
- Interpretable feature importance

#### Input Features
```python
features = {
    "soil_moisture": float,      # Current moisture percentage (0-100)
    "temperature": float,        # Celsius
    "humidity": float,           # Percentage (0-100)
    "hour_of_day": int,         # 0-23
    "day_of_week": int,         # 0-6
    "season": str,              # "spring", "summer", "fall", "winter"
    "historical_avg_moisture": float,  # Last 24h average
    "rainfall_last_24h": float  # mm (optional if weather API integrated)
}
```

#### Output Predictions
```python
predictions = {
    "irrigation_needed": bool,   # True/False
    "water_amount_liters": float,  # Predicted volume
    "confidence": float          # Model confidence (0-1)
}
```

#### Training Requirements
1. **Dataset**:
   - Minimum 1000 samples from historical irrigation data
   - Features: sensor readings + irrigation outcomes
   - Labels: Was irrigation successful? Water used?

2. **Model Training Pipeline**:
   ```python
   # Pseudocode structure
   - Load data from Firebase
   - Clean and preprocess (handle missing values, outliers)
   - Feature engineering (time-based features, rolling averages)
   - Train-test split (80-20)
   - Hyperparameter tuning (GridSearchCV)
   - Model evaluation (RMSE, MAE, R²)
   - Save model (pickle/joblib)
   - Version tracking
   ```

3. **Retraining**:
   - Admin-triggered retraining via dashboard
   - Scheduled weekly/monthly retraining
   - A/B testing new models vs production model

#### Model Files Structure
```
ml_model/
├── train.py              # Training script
├── predict.py            # Inference script
├── preprocessing.py      # Data cleaning utilities
├── model.pkl             # Saved Random Forest model
├── scaler.pkl            # Feature scaler
├── requirements.txt      # Python dependencies
└── config.yaml           # Model hyperparameters
```

---

## ⚙️ Backend Layer - FastAPI

### API Architecture

#### Framework: FastAPI
- Asynchronous request handling
- Automatic API documentation (Swagger/ReDoc)
- Built-in data validation (Pydantic)
- WebSocket support for real-time updates

#### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment variables
│   ├── models/
│   │   ├── user.py             # User data models
│   │   ├── sensor.py           # Sensor data models
│   │   └── irrigation.py       # Irrigation models
│   ├── routes/
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management
│   │   ├── sensors.py          # Sensor data endpoints
│   │   ├── irrigation.py       # Irrigation control
│   │   └── ml.py               # ML model endpoints
│   ├── services/
│   │   ├── firebase_service.py # Firebase operations
│   │   ├── auth_service.py     # JWT token handling
│   │   └── ml_service.py       # ML predictions
│   ├── middleware/
│   │   ├── auth.py             # Authentication middleware
│   │   └── cors.py             # CORS configuration
│   └── utils/
│       ├── validators.py       # Data validation
│       └── helpers.py          # Utility functions
├── tests/                      # Unit and integration tests
├── requirements.txt
├── Dockerfile
└── .env.example
```

### API Endpoints

#### Authentication Endpoints
```
POST   /api/v1/auth/register
Body: { "email": "user@example.com", "password": "***", "role": "farmer", "name": "John Doe" }
Response: { "message": "User registered successfully", "uid": "abc123" }

POST   /api/v1/auth/login
Body: { "email": "user@example.com", "password": "***" }
Response: { "access_token": "jwt_token", "user": {...}, "role": "farmer" }

POST   /api/v1/auth/logout
Headers: { "Authorization": "Bearer <token>" }
Response: { "message": "Logged out successfully" }

GET    /api/v1/auth/verify
Headers: { "Authorization": "Bearer <token>" }
Response: { "valid": true, "user": {...} }
```

#### User Management Endpoints
```
GET    /api/v1/users/profile
Headers: { "Authorization": "Bearer <token>" }
Response: { "uid": "abc", "email": "...", "role": "farmer", "devices": [...] }

PUT    /api/v1/users/profile
Body: { "name": "New Name", "phone": "..." }
Response: { "message": "Profile updated" }

GET    /api/v1/users           [ADMIN ONLY]
Response: { "users": [ {...}, {...} ] }

DELETE /api/v1/users/{uid}     [ADMIN ONLY]
Response: { "message": "User deleted" }
```

#### Sensor Data Endpoints
```
GET    /api/v1/sensors/latest
Query: ?device_id=device_001
Response: { "moisture": 45.2, "temperature": 28.5, "humidity": 65.3, "timestamp": ... }

GET    /api/v1/sensors/history
Query: ?device_id=device_001&start_date=2024-01-01&end_date=2024-01-31
Response: { "data": [ {...}, {...} ], "count": 1440 }

POST   /api/v1/sensors/health-check
Body: { "device_id": "device_001" }
Response: { "status": "healthy", "last_seen": "2024-01-15T10:30:00Z", "sensors": { "moisture": "ok", "temp": "ok" } }
```

#### Irrigation Control Endpoints
```
GET    /api/v1/irrigation/status
Query: ?device_id=device_001
Response: { "valve_open": false, "mode": "auto", "last_irrigation": "...", "duration_minutes": 20 }

POST   /api/v1/irrigation/manual-start
Body: { "device_id": "device_001", "duration_minutes": 15 }
Response: { "message": "Irrigation started", "stop_time": "..." }

POST   /api/v1/irrigation/manual-stop
Body: { "device_id": "device_001" }
Response: { "message": "Irrigation stopped", "duration_actual": 8 }

GET    /api/v1/irrigation/logs
Query: ?device_id=device_001&limit=50
Response: { "logs": [ { "start": "...", "end": "...", "water_used_liters": 120, "mode": "auto" }, ... ] }

GET    /api/v1/irrigation/predictions
Query: ?device_id=device_001&hours_ahead=48
Response: { "predictions": [ { "time": "2024-01-16T06:00", "irrigation_needed": true, "water_liters": 85 }, ... ] }
```

#### ML Model Endpoints
```
POST   /api/v1/ml/predict
Body: { "moisture": 35.0, "temperature": 32.0, "humidity": 55.0, "device_id": "device_001" }
Response: { "irrigation_needed": true, "water_amount_liters": 95.5, "confidence": 0.87 }

POST   /api/v1/ml/retrain        [ADMIN ONLY]
Body: { "dataset_start_date": "2024-01-01", "dataset_end_date": "2024-12-31" }
Response: { "message": "Retraining started", "job_id": "xyz789" }

GET    /api/v1/ml/model-info
Response: { "version": "1.2.0", "trained_date": "...", "accuracy": 0.92, "samples": 5000 }
```

#### Alerts Endpoints
```
GET    /api/v1/alerts/active
Query: ?device_id=device_001
Response: { "alerts": [ { "type": "critical_moisture", "message": "...", "timestamp": "..." }, ... ] }

PUT    /api/v1/alerts/{alert_id}/acknowledge
Response: { "message": "Alert acknowledged" }
```

### Authentication & Authorization

#### JWT Token Structure
```python
{
    "uid": "user_unique_id",
    "email": "user@example.com",
    "role": "farmer",  # "farmer", "middleman", "admin"
    "exp": 1704153600,  # Expiration timestamp
    "iat": 1704067200   # Issued at timestamp
}
```

#### Role-Based Access Control (RBAC)
```python
PERMISSIONS = {
    "farmer": [
        "view_own_sensors",
        "control_own_irrigation",
        "view_own_logs",
        "manual_override"
    ],
    "middleman": [
        "view_assigned_sensors",
        "view_assigned_logs",
        # No control permissions
    ],
    "admin": [
        "view_all_sensors",
        "view_all_users",
        "control_all_irrigation",
        "retrain_model",
        "manage_users",
        "export_data"
    ]
}
```

### Firebase Integration

#### Firestore Collections
```
users/
  {uid}/
    email: string
    name: string
    role: string
    devices: array
    created_at: timestamp

devices/
  {device_id}/
    owner_uid: string
    name: string
    location: string
    created_at: timestamp

sensor_readings/
  {device_id}/
    readings/
      {timestamp}/
        moisture: number
        temperature: number
        humidity: number

irrigation_logs/
  {device_id}/
    logs/
      {log_id}/
        start_time: timestamp
        end_time: timestamp
        water_used_liters: number
        mode: string (auto/manual)
        triggered_by: string (uid or "system")

alerts/
  {alert_id}/
    device_id: string
    type: string
    severity: string
    message: string
    acknowledged: boolean
    created_at: timestamp
```

#### Realtime Database Structure
```json
{
  "devices": {
    "device_001": {
      "sensors": {
        "moisture": 45.2,
        "temperature": 28.5,
        "humidity": 65.3,
        "timestamp": 1704067200
      },
      "status": {
        "valve_open": false,
        "mode": "auto",
        "last_seen": 1704067200,
        "health": "ok"
      },
      "commands": {
        "irrigation_command": "start",
        "duration": 900,
        "timestamp": 1704067200
      }
    }
  }
}
```

---

## 🎨 Frontend Layer - Web Dashboard

### Technology Stack
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Optional Libraries**:
  - Chart.js (for data visualization)
  - Socket.io (for real-time updates)
  - Tailwind CSS or Bootstrap (for responsive design)

### File Structure
```
frontend/
├── index.html              # Login page
├── register.html           # Registration page
├── dashboard.html          # Main dashboard (post-login)
├── css/
│   ├── styles.css          # Global styles
│   ├── login.css
│   └── dashboard.css
├── js/
│   ├── auth.js             # Login/logout/register logic
│   ├── api.js              # API calls wrapper
│   ├── dashboard.js        # Dashboard functionality
│   ├── charts.js           # Data visualization
│   └── realtime.js         # WebSocket/Firebase listeners
├── assets/
│   ├── images/
│   └── icons/
└── config.js               # Firebase and API configuration
```

### Page Layouts

#### 1. Login Page (`index.html`)
**Features**:
- Email and password input fields
- "Login" button
- Link to registration page
- "Forgot Password" link (optional)
- Error message display area

**UX**:
- Clean, minimal design
- Responsive (mobile-friendly)
- Form validation before submission

#### 2. Registration Page (`register.html`)
**Features**:
- Name, email, password, confirm password fields
- Role selection dropdown (Farmer, Middleman)
- "Register" button
- Link back to login
- Terms and conditions checkbox

**Validation**:
- Password strength indicator
- Email format validation
- Matching password confirmation

#### 3. Dashboard (`dashboard.html`)

##### Header/Navigation
- Logo and app name
- User profile dropdown (name, role, logout button)
- Navigation menu (different options per role)

##### Main Content Area (Role-Specific)

**FARMER Dashboard:**

**Section 1: Real-Time Sensor Data**
```html
┌─────────────────────────────────────────────┐
│  Current Conditions                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 🌡️ Temp  │  │ 💧 Humid │  │ 🌱 Moist │  │
│  │  28.5°C  │  │   65%    │  │   45%    │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

**Section 2: Irrigation Control**
```html
┌─────────────────────────────────────────────┐
│  Irrigation Control                         │
│                                             │
│  Status: 🟢 IDLE / 🔵 RUNNING              │
│  Mode: [Auto] [Manual]                      │
│                                             │
│  [Start Irrigation] [Stop Irrigation]       │
│  Duration: [15 mins ▼]                      │
└─────────────────────────────────────────────┘
```

**Section 3: Future Water Needs**
```html
┌─────────────────────────────────────────────┐
│  Predicted Water Requirements (48h)         │
│                                             │
│  📊 [Bar chart showing predicted needs]     │
│                                             │
│  Next irrigation: Jan 16, 6:00 AM           │
│  Estimated water: 95 liters                 │
└─────────────────────────────────────────────┘
```

**Section 4: Irrigation Logs**
```html
┌─────────────────────────────────────────────┐
│  Recent Irrigation History                  │
│                                             │
│  Date       | Start  | Duration | Water    │
│  ──────────────────────────────────────────│
│  Jan 15     | 06:00  | 20 min   | 120 L    │
│  Jan 14     | 18:30  | 15 min   | 90 L     │
│  ...                                        │
└─────────────────────────────────────────────┘
```

**Section 5: Alerts & Warnings**
```html
┌─────────────────────────────────────────────┐
│  ⚠️  CRITICAL: Soil moisture below 20%      │
│  🔴  ERROR: Temperature sensor disconnected │
└─────────────────────────────────────────────┘
```

**MIDDLEMAN Dashboard:**
- **Same as Farmer BUT**:
  - All control buttons disabled/hidden
  - "View Only" badge displayed
  - Can view multiple farmers' data (dropdown to switch)

**ADMIN Dashboard:**
- **All Farmer features +**:

**Additional Section: User Management**
```html
┌─────────────────────────────────────────────┐
│  User Management                            │
│                                             │
│  [Search users...]                          │
│                                             │
│  Email            | Role      | Devices     │
│  ─────────────────────────────────────────  │
│  farmer@test.com  | Farmer    | 2           │
│  helper@test.com  | Middleman | 0           │
│  [Edit] [Delete]                            │
└─────────────────────────────────────────────┘
```

**Additional Section: ML Model Management**
```html
┌─────────────────────────────────────────────┐
│  ML Model Controls                          │
│                                             │
│  Current Model: v1.2.0                      │
│  Accuracy: 92%
│  Last Trained: Jan 10, 2024                 │
│                                             │
│  [Retrain Model] [Download Training Data]   │
└─────────────────────────────────────────────┘
```

**Additional Section: System Health**
```html
┌─────────────────────────────────────────────┐
│  System Overview                            │
│                                             │
│  Total Devices: 15                          │
│  Active: 14 | Offline: 1                    │
│  Total Users: 23                            │
│                                             │
│  📊 [System health chart]                   │
└─────────────────────────────────────────────┘
```

### Critical UI/UX Requirements

#### Real-Time Updates
- Use Firebase Realtime Database listeners or WebSockets
- Update sensor values every 30-60 seconds without page refresh
- Show "Live" indicator when data is fresh (< 2 minutes old)

#### Alert System
- **Critical Alerts** (Red banner at top):
  - Soil moisture < 20%
  - Sensor disconnected/broken
  - Irrigation stuck ON for > max duration
- **Warning Alerts** (Yellow banner):
  - Soil moisture 20-30%
  - Device offline for > 5 minutes
- **Info Alerts** (Blue banner):
  - Irrigation scheduled soon
  - Model retrained successfully

#### Manual Irrigation Controls
```javascript
// When farmer clicks "Start Irrigation"
1. Show confirmation modal: "Start irrigation for 15 minutes?"
2. On confirm, disable button, show loading spinner
3. Send API request to backend
4. Backend writes command to Firebase
5. ESP32 reads command and starts irrigation
6. Dashboard updates status to "RUNNING"
7. Show countdown timer
8. Enable "Stop" button
```

#### Responsive Design
- Mobile-first approach
- Breakpoints: 320px (mobile), 768px (tablet), 1024px (desktop)
- Touch-friendly buttons (min 44px height)
- Collapsible navigation on mobile

#### Accessibility
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast mode option
- Minimum font size: 16px

---

## 🔐 Security Requirements

### Authentication
1. **Password Requirements**:
   - Minimum 8 characters
   - At least 1 uppercase, 1 lowercase, 1 number
   - Hashed using bcrypt (handled by Firebase Auth)

2. **JWT Tokens**:
   - 24-hour expiration
   - Refresh token mechanism
   - Stored in httpOnly cookies (if using cookies) or localStorage with XSS protection

3. **Session Management**:
   - Logout on all devices option
   - Automatic logout on token expiration
   - Remember me option (30-day token)

### Authorization
1. **Role-Based Access Control**:
   - Enforce permissions at both frontend (UI hiding) and backend (API validation)
   - Middleware to check user role before processing requests

2. **Device Ownership**:
   - Users can only access their own devices (except admin)
   - Middlemen assigned specific devices by admin

### Data Security
1. **API Communication**:
   - HTTPS only (enforce TLS 1.2+)
   - API key authentication for ESP32 devices
   - Rate limiting: 100 requests/minute per user

2. **Firebase Security Rules**:
```javascript
// Firestore Rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth.uid == userId || isAdmin();
    }
    match /devices/{deviceId} {
      allow read: if isOwner(deviceId) || isMiddlemanAssigned(deviceId) || isAdmin();
      allow write: if isOwner(deviceId) || isAdmin();
    }
  }
}

// Realtime Database Rules
{
  "rules": {
    "devices": {
      "$deviceId": {
        ".read": "auth != null && (isOwner($deviceId) || isAdmin())",
        ".write": "auth != null && (isOwner($deviceId) || isAdmin())"
      }
    }
  }
}
```

3. **Input Validation**:
   - Sanitize all user inputs (prevent XSS, SQL injection)
   - Validate sensor data ranges (reject impossible values)
   - Rate limit sensor data uploads (prevent flooding)

---

## 🚨 Alert System Specifications

### Alert Types

#### 1. Critical Alerts (Immediate Action Required)
```python
CRITICAL_ALERTS = {
    "moisture_critical": {
        "condition": "moisture < 20",
        "message": "CRITICAL: Soil moisture critically low!",
        "action": "Immediate irrigation recommended",
        "color": "red",
        "priority": 1
    },
    "sensor_failure": {
        "condition": "sensor_reading == null or out_of_range",
        "message": "ERROR: Sensor malfunction detected",
        "action": "Check sensor connections",
        "color": "red",
        "priority": 1
    },
    "irrigation_stuck": {
        "condition": "valve_open_duration > max_duration",
        "message": "CRITICAL: Irrigation system stuck ON",
        "action": "Manual intervention required",
        "color": "red",
        "priority": 1
    }
}
```

#### 2. Warning Alerts (Attention Needed)
```python
WARNING_ALERTS = {
    "moisture_low": {
        "condition": "20 <= moisture < 30",
        "message": "WARNING: Soil moisture low",
        "action": "Irrigation may be needed soon",
        "color": "yellow",
        "priority": 2
    },
    "device_offline": {
        "condition": "last_seen > 5_minutes_ago",
        "message": "WARNING: Device offline",
        "action": "Check device connectivity",
        "color": "yellow",
        "priority": 2
    },
    "high_temperature": {
        "condition": "temperature > 40",
        "message": "WARNING: High temperature detected",
        "action": "Monitor plants closely",
        "color": "yellow",
        "priority": 2
    }
}
```

#### 3. Info Alerts (Informational)
```python
INFO_ALERTS = {
    "irrigation_scheduled": {
        "message": "Irrigation scheduled in 2 hours",
        "color": "blue",
        "priority": 3
    },
    "model_updated": {
        "message": "ML model successfully updated",
        "color": "blue",
        "priority": 3
    }
}
```

### Alert Delivery Methods
1. **Dashboard Banner**: Persistent banner at top of dashboard
2. **Push Notifications**: Browser push notifications (optional)
3. **Email Alerts**: Send email for critical alerts (optional)
4. **SMS Alerts**: Send SMS for critical alerts (optional, requires integration)

### Alert Acknowledgment
- User can acknowledge alerts to remove from active list
- Acknowledged alerts moved to history
- Admin can view all alerts (acknowledged + active)

---

## 📊 Data Flow Examples

### Example 1: Automatic Irrigation Flow
```
1. ESP32 reads sensors → moisture=18%, temp=32°C, humidity=55%
2. ESP32 sends data to Firebase Realtime Database
3. Backend Cloud Function triggered on new data
4. Backend fetches data, calls ML model API
5. ML model predicts: irrigation_needed=True, water=100L
6. Backend writes command to Firebase: { irrigation_command: "start", duration: 600 }
7. ESP32 reads command from Firebase
8. ESP32 activates relay → solenoid valve opens
9. ESP32 updates status in Firebase: { valve_open: true, mode: "auto" }
10. Dashboard real-time listener updates UI: "Status: RUNNING"
11. After 10 minutes, ESP32 closes valve
12. ESP32 logs irrigation event to Firebase
13. Dashboard shows updated log entry
```

### Example 2: Manual Irrigation Flow
```
1. Farmer opens dashboard → sees current moisture=35%
2. Farmer switches to "Manual Mode"
3. Farmer clicks "Start Irrigation", selects 15 minutes
4. Confirmation modal appears: "Start irrigation for 15 minutes?"
5. Farmer confirms
6. Frontend sends POST /api/v1/irrigation/manual-start
7. Backend validates user permissions (is farmer?)
8. Backend writes command to Firebase: { irrigation_command: "start", duration: 900 }
9. ESP32 reads command, activates relay
10. Dashboard shows "Status: RUNNING (Manual)", countdown timer
11. After 15 minutes OR farmer clicks "Stop", irrigation stops
12. Backend logs manual irrigation event with triggered_by=uid
```

### Example 3: Alert Flow
```
1. ESP32 reads moisture=15% (critical)
2. Data sent to Firebase
3. Backend Cloud Function evaluates alert conditions
4. Condition met: moisture < 20
5. Backend creates alert document in Firestore
6. Backend sends push notification to farmer's browser
7. Dashboard real-time listener detects new alert
8. Dashboard displays red banner: "CRITICAL: Soil moisture critically low!"
9. Farmer acknowledges alert → alert moved to history
```

---

## 🧪 Testing Requirements

### Unit Tests
- **Backend**: Test all API endpoints, authentication, ML predictions
- **ESP32**: Test sensor reading functions, relay control, Firebase communication
- **ML Model**: Test prediction accuracy, edge cases (extreme values)

### Integration Tests
- **"