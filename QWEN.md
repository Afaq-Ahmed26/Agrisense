# QWEN.md

## 1. Project Overview:

AgriSense is a production-ready cloud + IoT + ML smart irrigation system. It optimizes agricultural water usage by combining hardware sensors, machine learning predictions, and real-time web controls. The system automates irrigation based on real-time data and ML predictions, allows remote monitoring via a web dashboard, supports multi-user roles (Farmer, Middleman, Admin), and provides critical alerts for system failures and irrigation needs.

## 2. Technology Stack:

-   **Hardware**: ESP32, Soil Moisture Sensors, Temperature & Humidity Sensors (DHT22), Relay Module, Solenoid Valves
-   **ML Model**: Python, scikit-learn (Random Forest Regression)
-   **Backend**: Python, FastAPI
-   **Database**: Firebase (Firestore, Realtime Database)
-   **Frontend**: HTML, CSS, JavaScript (ES6+)
-   **Communication**: HTTPS, WebSockets, MQTT
-   **Other**: Pydantic, bcrypt (via Firebase Auth)

## 3. Directory Structure:

```
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── sensor.py
│   │   │   └── irrigation.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── sensors.py
│   │   │   ├── irrigation.py
│   │   │   └── ml.py
│   │   ├── services/
│   │   │   ├── firebase_service.py
│   │   │   ├── auth_service.py
│   │   │   └── ml_service.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   └── cors.py
│   │   └── utils/
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── tests/
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── register.html
│   ├── dashboard.html
│   ├── css/
│   │   ├── styles.css
│   │   ├── login.css
│   │   └── dashboard.css
│   ├── js/
│   │   ├── auth.js
│   │   ├── api.js
│   │   ├── dashboard.js
│   │   ├── charts.js
│   │   └── realtime.js
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   └── config.js
└── ml_model/
    ├── train.py
    ├── predict.py
    ├── preprocessing.py
    ├── model.pkl
    ├── scaler.pkl
    ├── requirements.txt
    └── config.yaml
```

## 4. Coding Conventions:

-   **Backend (FastAPI)**: Follow FastAPI and Pydantic standards for data models, validation, and API routes. Use standard Python conventions (PEP 8). Asynchronous operations should be handled efficiently.
-   **Frontend (JavaScript)**: Use ES6+ syntax. Employ clear naming conventions for variables, functions, and event handlers. Prefer modular JavaScript for organization. Use semantic HTML and CSS best practices.
-   **Hardware (ESP32)**: Use standard Arduino framework for ESP32. Code should be well-commented, particularly for sensor reading, relay control, and communication logic. Employ non-blocking delays and implement robust error handling.
-   **ML Model (Python)**: Follow standard Python data science and ML practices. Use clear naming for features, models, and parameters. Comment complex logic and assumptions.
-   **General**: Maintain consistency across all layers. Use clear, descriptive names for files, functions, variables, and classes.

## 5. Key Commands:

-   **Backend**:
    -   `uvicorn backend.app.main:app --reload` (Run development server)
    -   `pytest backend/tests/` (Run backend tests)
    -   `docker build -t agrisense-backend .` (Build Docker image)
-   **ML Model**:
    -   `python ml_model/train.py` (Train the ML model)
    -   `python ml_model/predict.py --input_data <data>` (Run inference)
-   **Frontend**:
    -   Serve `frontend/` directory using a simple HTTP server (e.g., `python -m http.server` in the `frontend` directory).
-   **ESP32**:
    -   Compile and upload firmware using Arduino IDE or PlatformIO.

## 6. Important Notes:

-   **Security**:
    -   All API communication must use HTTPS.
    -   Firebase security rules are critical for data access control. Ensure they are correctly configured for all Firestore and Realtime Database collections.
    -   JWT tokens have a 24-hour expiration. Implement refresh token logic.
    -   Sanitize all user inputs to prevent XSS and other injection attacks.
    -   API rate limiting is in place.
-   **Dependencies**:
    -   Ensure all Python dependencies are installed via `requirements.txt` for backend and ML model.
    -   Node.js and npm/yarn are likely needed for frontend development if using additional JS libraries not listed.
    -   Arduino IDE or PlatformIO is required for ESP32 firmware development.
-   **Firebase Configuration**: The `config.js` (frontend), `.env.example` (backend), and `ml_model/config.yaml` files need to be populated with actual Firebase project credentials and API keys.
-   **ESP32 Credentials**: WiFi credentials and Firebase project details must be securely programmed into the ESP32 firmware (e.g., via `config.h` or environment variables during build).
-   **ML Model Retraining**: Model retraining can be triggered via the Admin dashboard or scheduled weekly/monthly. Ensure the training dataset is sufficient and diverse.
