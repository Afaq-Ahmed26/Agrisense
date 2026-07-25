# AgriSense – ML Powered Smart Irrigation System

AgriSense is an IoT based smart irrigation system that automates water management using real time sensor data, machine learning predictions, and a live monitoring dashboard. The system reduces water wastage and improves crop yield by triggering irrigation only when needed, based on soil, temperature, and humidity conditions.

---

## 📌 Features

- **IoT Sensor Integration** – ESP32 microcontroller collects real time soil moisture, temperature, and humidity data
- **Automated Irrigation** – Relay controlled water pump triggered automatically based on ML driven predictions
- **ML-Based Predictions** – Soil, temperature, and humidity data used to predict optimal irrigation schedules
- **Real-Time Data Pipeline** – Live sensor data streamed and stored using PostgreSQL and Firebase
- **Web Dashboard** – Vue.js dashboard with Chart.js for real time data visualization and historical trends
- **Secure Authentication** – JWT-based secure login and role-based access control
- **REST API Backend** – FastAPI backend for handling sensor data, predictions, and user requests

---

## 🛠️ Tech Stack

| Layer            | Technology                          |
|------------------|--------------------------------------|
| Microcontroller  | ESP32                                |
| Backend          | FastAPI                              |
| Database         | PostgreSQL                           |
| Authentication   | Firebase                             |
| Frontend         | Vue.js                               |
| Visualization    | Chart.js                             |
| Authentication   | JWT (JSON Web Tokens)                |
| Hardware Control | Relay Module (Water Pump)            |

---

## 🏗️ System Architecture

```
ESP32 Sensors (Soil/Temp/Humidity)
        │
        ▼
  FastAPI Backend  ──────► PostgreSQL / Firebase
        │                        (Data Storage)
        ▼
  ML Prediction Engine
        │
        ▼
  Relay-Controlled Water Pump
        │
        ▼
  Vue.js Dashboard (Chart.js) ◄──── JWT Auth
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Firebase project credentials
- ESP32 board with Arduino IDE / PlatformIO

### Backend Setup (FastAPI)
```bash
git clone https://github.com/Afaq-Ahmed26/Agrisense.git
cd agrisense/backend

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Update DATABASE_URL, FIREBASE_CREDENTIALS, JWT_SECRET_KEY, etc.

# Run database migrations
alembic upgrade head

# Start the server
uvicorn main:app --reload
```

### Frontend Setup (Vue.js)
```bash
cd agrisense/frontend

npm install
npm run serve
```

### ESP32 Firmware Setup
1. Open the `firmware/` folder in Arduino IDE or PlatformIO
2. Update WiFi credentials and backend API endpoint in `config.h`
3. Flash the firmware to the ESP32 board
4. Connect soil moisture, temperature, and humidity sensors as per the wiring diagram in `/docs`

---

## 🔐 Environment Variables

Create a `.env` file in the backend directory with the following:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/agrisense
FIREBASE_CREDENTIALS=path/to/firebase-credentials.json
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 📡 API Overview

| Method | Endpoint              | Description                          |
|--------|------------------------|---------------------------------------|
| POST   | `/auth/login`          | Authenticate user, returns JWT token |
| POST   | `/auth/register`       | Register a new user                  |
| GET    | `/sensors/data`        | Fetch latest sensor readings         |
| POST   | `/sensors/data`        | Push sensor data from ESP32          |
| GET    | `/irrigation/status`   | Get current pump status              |
| POST   | `/irrigation/trigger`  | trigger irrigation                   |
| GET    | `/predictions`         | Get ML based irrigation predictions  |

---

## 📄 License

This project is developed as a Final Year Project at the University of Education, Lahore, Department of Information Sciences.

---
