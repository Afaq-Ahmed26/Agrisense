# CLAUDE.md

## 1. Project Overview:

AgriSense is a production-ready cloud + IoT + ML smart irrigation system. It optimizes agricultural water usage by combining hardware sensors, machine learning predictions, and real-time web controls. The system automates irrigation based on real-time data and ML predictions, allows remote monitoring via a web dashboard, supports multi-user roles (Farmer, Middleman, Admin), and provides critical alerts for system failures and irrigation needs.

## 2. Technology Stack:

-   **Hardware**: ESP32, Soil Moisture Sensors, Temperature & Humidity Sensors (DHT22), Relay Module, Solenoid Valves
-   **ML Model**: Python, scikit-learn (Random Forest Regression)
-   **Backend**: Python, FastAPI
-   **Database**: Firebase (Firestore, Realtime Database)
-   **Frontend**: Vue.js 3, Vite, JavaScript (ES6+), Bootstrap, Chart.js
-   **Communication**: HTTPS, WebSockets, MQTT
-   **Other**: Pydantic, bcrypt (via Firebase Auth)

## 3. Directory Structure:

```
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   └── cors.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── sensor.py
│   │   │   └── irrigation.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── sensors.py
│   │   │   ├── irrigation.py
│   │   │   └── ml.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── firebase_service.py
│   │   │   ├── auth_service.py
│   │   │   └── ml_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── source/
│   ├── venv/
│   ├── venv,/
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── start_server.py
│   └── test_firebase.py
├── Frontend/
│   ├── Fire-base.md
│   ├── FRONTEND_FEATURES.md
│   ├── README.md
│   ├── dist/
│   ├── index.html
│   ├── mock-server.js
│   ├── node_modules/
│   ├── package-lock.json
│   ├── package-mock.json
│   ├── package.json
│   ├── public/
│   │   ├── favicon.ico
│   │   └── vite.svg
│   ├── src/
│   │   ├── App.vue
│   │   ├── assets/
│   │   │   ├── logo.png
│   │   │   └── vue.svg
│   │   ├── components/
│   │   │   ├── HelloWorld.vue
│   │   │   ├── LoginView.vue
│   │   │   ├── RegisterView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── NavigationBar.vue
│   │   │   ├── ProfileView.vue
│   │   │   ├── UpdateProfileView.vue
│   │   │   ├── UserManagementView.vue
│   │   │   └── ReportsView.vue
│   │   ├── config.js
│   │   ├── css/
│   │   │   ├── dashboard.css
│   │   │   └── login.css
│   │   ├── main.js
│   │   ├── router.js
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── auth-service.js
│   │   │   ├── mock-api.js
│   │   │   └── mock-data.js
│   │   ├── store/
│   │   │   └── index.js
│   │   ├── utils/
│   │   │   └── constants.js
│   │   └── views/
│   │       ├── HomeView.vue
│   │       └── AboutView.vue
│   └── vite.config.mjs
├── node_modules/
├── venv/
├── .gitignore
├── backend.md
├── chotay.md
├── CLAUDE.md
├── FRONTEND_BACKEND_SETUP.md
├── G.md
├── GEMINI_CONTEXT.md
├── package-lock.json
├── package.json
├── Project-Overview.md
├── Q.md
├── QWEN.md
└── TODAY.md
```

## 4. Coding Conventions:

-   **Backend (FastAPI)**: Follow FastAPI and Pydantic standards for data models, validation, and API routes. Use standard Python conventions (PEP 8). Asynchronous operations should be handled efficiently.
-   **Frontend (Vue.js)**: Use Vue 3 Composition API with JavaScript. Employ clear naming conventions for components, functions, and event handlers. Prefer modular JavaScript for organization. Use semantic HTML and CSS best practices.
-   **Hardware (ESP32)**: Use standard Arduino framework for ESP32. Code should be well-commented, particularly for sensor reading, relay control, and communication logic. Employ non-blocking delays and implement robust error handling.
-   **ML Model (Python)**: Follow standard Python data science and ML practices. Use clear naming for features, models, and parameters. Comment complex logic and assumptions.
-   **General**: Maintain consistency across all layers. Use clear, descriptive names for files, functions, variables, and classes.

## 5. Key Commands:

-   **Backend**:
    -   `python start_server.py` (Run development server)
    -   `pytest backend/tests/` (Run backend tests)
    -   `docker build -t agrisense-backend .` (Build Docker image)
-   **ML Model**:
    -   `python ml_model/train.py` (Train the ML model)
    -   `python ml_model/predict.py --input_data <data>` (Run inference)
-   **Frontend**:
    -   `npm run dev` (Run development server)
    -   `npm run build` (Build for production)
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
    -   Node.js and npm are needed for frontend development.
    -   Arduino IDE or PlatformIO is required for ESP32 firmware development.
-   **Firebase Configuration**: The `config.js` (frontend), `.env.example` (backend), and `ml_model/config.yaml` files need to be populated with actual Firebase project credentials and API keys.
-   **ESP32 Credentials**: WiFi credentials and Firebase project details must be securely programmed into the ESP32 firmware (e.g., via `config.h` or environment variables during build).
-   **ML Model Retraining**: Model retraining can be triggered via the Admin dashboard or scheduled weekly/monthly. Ensure the training dataset is sufficient and diverse.
