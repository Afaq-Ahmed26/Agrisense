# CLAUDE.md

## 1. Project Overview:

AgriSense is a production-ready cloud + IoT + ML smart irrigation system. It optimizes agricultural water usage by combining hardware sensors, machine learning predictions, and real-time web controls. The system automates irrigation based on real-time data and ML predictions, allows remote monitoring via a web dashboard, supports multi-user roles (Farmer, Middleman, Admin), and provides critical alerts for system failures and irrigation needs. The system is designed to work with simulated data during development and seamlessly transition to real hardware when available.

## 2. Technology Stack:

-   **Hardware**: ESP32, Soil Moisture Sensors, Temperature & Humidity Sensors (DHT22), Relay Module, Solenoid Valves (with simulation support)
-   **ML Model**: Python, scikit-learn (Random Forest Regression)
-   **Backend**: Python, FastAPI
-   **Database**: Firebase (Firestore, Realtime Database) with mock services for development
-   **Frontend**: Vue.js 3, Vite, JavaScript (ES6+), Bootstrap, Chart.js, Firebase
-   **Communication**: HTTPS, WebSockets
-   **Other**: Pydantic, bcrypt, Firebase Authentication

## 3. Directory Structure:

```
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   └── cors.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── sensor.py
│   │   │   ├── irrigation.py
│   │   │   ├── ml.py
│   │   │   ├── activity_log.py
│   │   │   ├── notification.py
│   │   │   ├── notification_preferences.py
│   │   │   ├── preferences.py
│   │   │   ├── thresholds.py
│   │   │   └── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── sensors.py
│   │   │   ├── irrigation.py
│   │   │   ├── ml.py
│   │   │   ├── alerts.py
│   │   │   ├── notifications.py
│   │   │   ├── activity_logs.py
│   │   │   └── thresholds.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── firebase_service.py
│   │   │   ├── mock_firebase_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── ml_service.py
│   │   │   ├── sensor_service.py
│   │   │   ├── irrigation_service.py
│   │   │   ├── sensor_simulation.py
│   │   │   ├── user_service.py
│   │   │   ├── alert_service.py
│   │   │   ├── notification_service.py
│   │   │   └── activity_log_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       └── helpers.py
│   ├── .env.example
│   ├── requirements.txt
│   ├── start_server.py
│   └── test_firebase.py
├── Frontend/
│   ├── Fire-base.md
│   ├── FRONTEND_FEATURES.md
│   ├── README.md
│   ├── dist/
│   ├── index.html
│   ├── node_modules/
│   ├── package-lock.json
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
│   │   │   ├── AlertsBanner.vue
│   │   │   ├── IrrigationControl.vue
│   │   │   ├── PredictionChart.vue
│   │   │   ├── SensorDisplay.vue
│   │   │   └── LogsTable.vue
│   │   ├── config.js
│   │   ├── css/
│   │   │   └── main.css
│   │   ├── main.js
│   │   ├── router.js
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   ├── auth.js
│   │   │   ├── firebase.js
│   │   │   ├── firebaseConfig.js
│   │   │   ├── mock-api.js
│   │   │   └── mock-data.js
│   │   ├── store/
│   │   │   ├── auth.js
│   │   │   └── notifications.js
│   │   ├── utils/
│   │   │   ├── helpers.js
│   │   │   ├── unitConverter.js
│   │   │   └── validation.js
│   │   └── views/
│   │       ├── ActivityLogView.vue
│   │       ├── Admin/
│   │       │   └── ThresholdsView.vue
│   │       ├── ConnectDeviceView.vue
│   │       ├── DashboardView.vue
│   │       ├── DeleteAccountConfirmView.vue
│   │       ├── ForgotPasswordView.vue
│   │       ├── LoginView.vue
│   │       ├── NotificationsView.vue
│   │       ├── ProfileView.vue
│   │       ├── RegisterView.vue
│   │       ├── ReportsView.vue
│   │       ├── UpdateProfileView.vue
│   │       └── UserManagementView.vue
│   └── vite.config.mjs
├── .gitignore
├── backend.md
├── CLAUDE.md
├── FRONTEND_BACKEND_SETUP.md
├── Firebase.md
├── GEMINI.md
├── GEMINI_CONTEXT.md
├── Project-Overview.md
├── Project-structure.md
├── Q.md
├── QWEN.md
├── TODAY.md
├── chotay.md
├── refactor.md
└── sess.md
```

## 4. Coding Conventions:

-   **Backend (FastAPI)**: Follow FastAPI and Pydantic standards for data models, validation, and API routes. Use standard Python conventions (PEP 8). Asynchronous operations should be handled efficiently. Use dependency injection for authentication and authorization.
-   **Frontend (Vue.js)**: Use Vue 3 Composition API with JavaScript. Employ clear naming conventions for components, functions, and event handlers. Prefer modular JavaScript for organization. Use semantic HTML and CSS best practices. Leverage Firebase for real-time updates and authentication.
-   **Services**: Separate business logic into service classes to maintain clean separation of concerns.
-   **ML Model (Python)**: Follow standard Python data science and ML practices. Use clear naming for features, models, and parameters. Comment complex logic and assumptions.
-   **General**: Maintain consistency across all layers. Use clear, descriptive names for files, functions, variables, and classes.

## 5. Key Commands:

-   **Backend**:
    -   `python start_server.py` (Run development server with sensor simulation)
    -   `uvicorn app.main:app --reload` (Alternative development server)
    -   `pytest backend/tests/` (Run backend tests)
    -   `docker build -t agrisense-backend .` (Build Docker image)
-   **Frontend**:
    -   `npm install` (Install dependencies)
    -   `npm run dev` (Run development server)
    -   `npm run build` (Build for production)
    -   `npm run preview` (Preview production build)
-   **Environment**:
    -   Create `.env` file with Firebase credentials for production use
    -   The system automatically falls back to mock services when Firebase credentials are not provided

## 6. Important Notes:

-   **Security**:
    -   All API communication must use HTTPS in production.
    -   Firebase security rules are critical for data access control. Ensure they are correctly configured for all Firestore and Realtime Database collections.
    -   JWT tokens are used for session management with Firebase Authentication.
    -   Sanitize all user inputs to prevent XSS and other injection attacks.
    -   API rate limiting is implemented through Firebase and application-level controls.
-   **Development Features**:
    -   The system includes comprehensive mock services for development without hardware or Firebase
    -   Sensor simulation automatically generates realistic data for testing
    -   Frontend automatically falls back to mock data when backend is unavailable
    -   Includes real-time dashboard with live sensor data updates
-   **Dependencies**:
    -   Ensure all Python dependencies are installed via `requirements.txt` for backend
    -   Node.js and npm are needed for frontend development
    -   Firebase credentials are required for production deployment
-   **Configuration**: The system uses environment variables for configuration and automatically falls back to default values for development
-   **ML Model Integration**: The backend includes endpoints for ML model integration with placeholder implementations ready for model deployment
