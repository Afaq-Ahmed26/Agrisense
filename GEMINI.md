# AgriSense Project Overview

This document provides a comprehensive overview of the AgriSense project, including its architecture, key functionalities, recent development efforts, and remaining challenges.

## 1. Project Overview

AgriSense is a smart irrigation system designed to provide users with tools for managing user profiles, sensor data, irrigation schedules, and notifications. A core component is a machine learning model that provides predictions to optimize irrigation. The system is built with a FastAPI backend, a Vue.js frontend, and a Python-based machine learning model.

## 2. Architecture

The project follows a typical full-stack architecture with distinct frontend, backend, and machine learning components.

### Frontend (Vue.js 3 + Vite)

*   **Purpose:** Serves as the user interface for interacting with the AgriSense system. It allows users to view sensor data, control irrigation, manage their profiles, and receive notifications.
*   **Technologies:** Vue.js 3, Vite (build tool), Bootstrap (UI framework), Chart.js (data visualization), FontAwesome (icons), Axios (HTTP client).
*   **Key Modules/Files:**
    *   `App.vue`: Main application component.
    *   `src/services/auth.js`: Handles frontend authentication logic, including Firebase ID token refreshing.
    *   `src/store/auth.js`: Vuex store module for managing authentication state (`authStore.user`).
    *   `src/services/api.js`: Provides an interface for making API calls to the backend.
    *   `src/services/mock-api.js`: Offers fallback mock data for development or when API calls fail.
    *   `src/router.js`: Manages client-side routing within the Vue application.
*   **Authentication:** Integrates with Firebase for user authentication, specifically utilizing Firebase ID tokens for secure backend communication.

### Backend (FastAPI + Python)

*   **Purpose:** The central hub of the AgriSense system, providing a RESTful API for all functionalities. It handles business logic, data persistence, and integration with the machine learning model.
*   **Technologies:** FastAPI (web framework), Uvicorn (ASGI server), `firebase-admin` (Firestore integration), `python-jose` (JWT handling - though customized for Firebase tokens), `passlib` (password hashing), `python-dotenv` (environment variable management), Pydantic (data validation), `pandas`, `scikit-learn` (for ML service interactions).
*   **Key Modules/Files:**
    *   `app/main.py`: The main entry point for the FastAPI application, where routers are included, CORS is configured, and global endpoints like `/` and `/health` are defined.
    *   `app/routes/`: Contains separate modules for different API endpoint categories (e.g., `auth.py`, `users.py`, `sensors.py`, `irrigation.py`, `ml.py`, `alerts.py`, `notifications.py`, `activity_logs.py`, `thresholds.py`).
    *   `app/services/`: Implements business logic and integrations with external services (e.g., `auth_service.py` for token verification, `firebase_service.py` for Firestore interactions, `user_service.py` for user-related operations, `ml_service.py` for ML model integration).
    *   `app/models/`: Defines data models using Pydantic for request/response validation and database schema representation (e.g., `user.py`, `sensor.py`, `irrigation.py`).
*   **Database:** Primarily uses Google Cloud Firestore for data persistence, accessed via the `firebase-admin` SDK.
*   **Authentication/Authorization:** Authenticates users using Firebase ID tokens. The backend's `auth_service.py` has been adapted to verify these tokens, which are signed with `RS256` by Firebase.
*   **CORS:** Configured in `app/main.py` to allow all origins, which is suitable for development but needs to be restricted to specific frontend origins in a production environment.

### Machine Learning Model (`model/`)

*   **Purpose:** Develops and stores the machine learning model responsible for predicting optimal irrigation parameters.
*   **Technologies:** Python, `scikit-learn` (for `RandomForestRegressor`), `pandas` (for data handling), `joblib` (for model serialization).
*   **Key Modules/Files:**
    *   `train_model.py`: A Python script that loads data from `system_data.csv`, trains a `RandomForestRegressor` model using features like 'Soil Moisture (%)', 'Temperature (°C)', 'Humidity (%)', 'Light Level (lx)', and a target 'Valve Duration (s)', and then saves the trained model.
    *   `irrigation_model.pkl`: The serialized (pickled) `RandomForestRegressor` model, ready for deployment and inference.
    *   `system_data.csv`: The dataset used to train the irrigation prediction model.
*   **Integration:** The backend's `ml` router and `ml_service.py` are designed to load and utilize this trained model for making predictions.

## 3. Key Functionalities

*   **User Profile Management:** Users can register, log in, view, and update their profiles.
*   **Sensor Data Handling:** Management of various agricultural sensors, including data collection and display.
*   **Irrigation Control:** Features for scheduling and controlling irrigation systems.
*   **Machine Learning Predictions:** Provides predictive capabilities for optimizing irrigation based on environmental and sensor data.
*   **Alerts and Notifications:** System-generated alerts and user-specific notifications for critical events or updates.
*   **Activity Logging:** Comprehensive logging of user actions and system events.
*   **Threshold Management:** Configuration of thresholds for sensor readings or other parameters to trigger alerts or actions.

## 4. Recent Development & Debugging Efforts (from Day 16 Session Summary)

Recent efforts have focused heavily on debugging and refining the authentication and user profile display aspects of the application.

*   **Problem:** Frontend initially displayed "John Farmer" for all users due to a fallback to mock data.
*   **Resolved Issues:**
    *   **Firebase ID Token Refresh:** The frontend (`Frontend/src/services/auth.js`) was modified to explicitly refresh Firebase ID tokens (`user.getIdToken(true)`) to ensure valid tokens are sent to the backend.
    *   **JWT Verification Logic:** The backend's `auth_service.py` was updated to correctly verify Firebase ID tokens, replacing a problematic custom `HS256` implementation with one that handles Firebase's `RS256` signed tokens by fetching Google's public keys.
    *   **Firebase Admin SDK Configuration:** Issues related to quoting (`FIREBASE_ADMIN_SDK_CONFIG`) in `backend/.env` were resolved by externalizing the credentials to `backend/firebase-credentials.json` and pointing to this file via `FIREBASE_CONFIG_PATH`. The `FIREBASE_PROJECT_ID` was also added to `.env`.
    *   **`FirebaseService` Initialization:** Refactored logic in `firebase_service.py` to correctly prioritize and initialize Firebase Admin SDK using the specified configuration path.
    *   **User ID Extraction:** Backend endpoints across `users.py`, `notifications.py`, and `activity_logs.py` were corrected to use `"user_id"` instead of `"uid"` when extracting the user identifier from Firebase token payloads.

*   **Identified Pending Issues:**
    *   **ML Features Temporarily Disabled:** The machine learning prediction features have been temporarily disabled in the frontend (`DashboardView.vue`) to focus on ensuring stable single-sensor data integration and display. The current focus is on correctly displaying soil moisture sensor data.
    *   **`sensor_data_generator.py` Firebase Sign-in:** The `sensor_data_generator.py` script is reportedly experiencing issues signing into Firebase.
    *   **CORS Errors:** While some CORS issues were implicitly resolved, ongoing CORS errors are considered a symptom of deeper backend query failures (related to missing Firestore indexes).

## 5. Development Environment Details

*   **Python (Backend & ML):** Dependencies managed via `backend/requirements.txt` and installed in virtual environments (e.g., `venv/`, `source/`).
*   **JavaScript/Node.js (Frontend):** Dependencies managed via `Frontend/package.json` and installed in `node_modules/`.
*   **Configuration:** Environment variables, particularly in `backend/.env`, are critical for configuring Firebase, JWTs, and other application settings.
Session ID: 2026-03-08T17:15:30Z