# Day 16

## Session Summary: Frontend User Profile Debugging

**Issue:** Users logging into the system were consistently seeing "John Farmer" details in the frontend, rather than their actual profile information, despite successful authentication. Other user accounts were also not displaying correctly.

**Investigation & Debugging Steps:**

1.  **Initial Frontend Analysis (`App.vue`, `auth.js`, `store/auth.js`):**
    *   Confirmed `userName` and `userRole` in `App.vue` derived from `authStore.user`.
    *   Verified `authStore.user` is populated by `fetchUser()` in `store/auth.js`, which calls `apiService.getMe()`.
    *   Identified that `apiService.getMe()` (in `api.js`) calls the backend's `GET /users/me` endpoint.
    *   Discovered `apiService` has a fallback to `mockApiService.getUserProfile()` if real API calls fail.
    *   Confirmed `mockApiService.getUserProfile()` (in `mock-api.js`) returns `MOCK_USERS[0]`, which contains "John Farmer" data.

2.  **Backend User Service Check (`user_service.py`, `users.py`):**
    *   Verified `GET /users/me` in `backend/app/routes/users.py` correctly extracts `uid` from the token and calls `get_user_from_firestore(uid)`.
    *   Server logs confirmed `get_user_from_firestore` was returning the correct user data (e.g., "Afaq Ahmed"). This ruled out a backend data retrieval issue.

3.  **Frontend Authentication Flow Refinement (`auth.js`):**
    *   Hypothesized that `GET /users/me` was failing due to an expired token, triggering the mock fallback.
    *   Modified `Frontend/src/services/auth.js` to force a refresh of the Firebase ID token (`user.getIdToken(true)`) within the `onAuthStateChanged` listener. This aimed to ensure the frontend always sent a fresh token to the backend.

4.  **Backend JWT Verification Debugging (`auth_service.py`):**
    *   Frontend still received `403 Forbidden` errors for `/users/me` requests after the Firebase token refresh change.
    *   Added detailed logging to `backend/app/services/auth_service.py`'s `verify_token` function to capture `JWTError` details.
    *   Backend logs then revealed the specific error: `ERROR: JWT verification failed: The specified alg value is not allowed`.
    *   This error implies a mismatch or problem with the `JWT_SECRET_KEY` or `JWT_ALGORITHM` used for JWT signing/verification in the `jose` library. Both `create_access_token` and `verify_token` explicitly use `settings.JWT_ALGORITHM` (HS256) and `settings.JWT_SECRET_KEY`. The default `JWT_SECRET_KEY` ("your-secret-key-change-in-production") is often too weak or triggers strict checks in `jose`.

## Session Summary: Firebase and JWT Authentication Fixes

**Initial State:**
*   Backend showing "Firebase credentials not configured. Using mock service."
*   Backend showing `ERROR: JWT verification failed: The specified alg value is not allowed`.
*   Frontend receiving `403 Forbidden` errors due to failed backend authentication.
*   Frontend showing "John Farmer" due to fallback to mock data.

**Problem Identification & Resolution Steps:**

1.  **`FIREBASE_ADMIN_SDK_CONFIG` Quoting:**
    *   **Problem:** `FIREBASE_ADMIN_SDK_CONFIG` in `backend/.env` was quoted with single quotes, causing JSON parsing errors (`Expecting ',' delimiter`).
    *   **Fix:** Removed the single quotes around the JSON value in `backend/.env`. (Attempted to fix newline escaping but this was superseded by a better approach).

2.  **Firebase Credential Management (Best Practice Adoption):**
    *   **Problem:** Embedding the Firebase Admin SDK JSON directly into `.env` is insecure and prone to formatting errors, especially with multiline private keys.
    *   **Fix:**
        *   Extracted the Firebase Admin SDK JSON content into a new file: `backend/firebase-credentials.json`.
        *   Updated `backend/.env` to point to this file using `FIREBASE_CONFIG_PATH=./firebase-credentials.json` and removed the raw `FIREBASE_ADMIN_SDK_CONFIG` content.

3.  **Missing `FIREBASE_PROJECT_ID`:**
    *   **Problem:** The `FirebaseService` in `firebase_service.py` was failing to initialize with real Firebase because `settings.FIREBASE_PROJECT_ID` was not set, causing it to fall back to mock services.
    *   **Fix:** Added `FIREBASE_PROJECT_ID=agrisense-ue` to `backend/.env`, extracting the project ID from `backend/firebase-credentials.json`.

4.  **`FirebaseService` Initialization Logic:**
    *   **Problem:** The `if` condition in `FirebaseService.__init__` in `firebase_service.py` was not correctly prioritizing `FIREBASE_CONFIG_PATH`, leading to mock service fallback even when the path was set.
    *   **Fix:** Refactored the `if` condition in `firebase_service.py` to prioritize `settings.FIREBASE_CONFIG_PATH` correctly.

5.  **JWT Algorithm Mismatch (`HS256` vs `RS256`):**
    *   **Problem:** The backend was configured to verify JWTs using `HS256` (symmetric algorithm with `JWT_SECRET_KEY`), but the frontend's Firebase ID tokens are signed with `RS256` (asymmetric algorithm using public keys). A typo (`HS26` instead of `HS256`) was initially present in `.env`.
    *   **Fix:**
        *   Modified `backend/app/services/auth_service.py` to replace the custom `verify_token` logic with one that fetches Google's public keys and verifies Firebase ID tokens using `RS256`.
        *   Removed `create_access_token`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` from `backend/.env` and `auth_service.py` as they are no longer needed for Firebase-based authentication.

6.  **UID Extraction Error in Endpoints:**
    *   **Problem:** Several backend endpoints (e.g., `/users/me`, `/notifications`, `/activity-logs`) were attempting to extract the user ID from the Firebase token payload using `user_payload.get("uid")`, but the correct key in the Firebase payload is `"user_id"`.
    *   **Fix:** Changed all instances of `user_payload.get("uid")` to `user_payload.get("user_id")` in `backend/app/routes/users.py`, `backend/app/routes/notifications.py`, and `backend/app/routes/activity_logs.py`.

7.  **Missing Firestore Indexes:**
    *   **Problem:** Queries to Firestore for `/notifications` and `/activity-logs` were failing with `FailedPrecondition: 400 The query requires an index.` because necessary composite indexes had not been created in the Firebase project.
    *   **Action:** Provided the user with the exact URLs to create the required composite indexes in the Firebase Console. This is a manual step for the user.

**Current Status:**
*   Firebase initialization and ID token verification are working.
*   Most core API endpoints (`/users/me`, `/alerts`, user/notification preferences) are now `200 OK`.
*   The `sensor_data_generator.py` script still has an issue signing into Firebase.
*   The `get_all_activity_logs` endpoint is now hitting the database, but is encountering a `FailedPrecondition` error due to a missing composite Firestore index, which the user needs to create manually. The `notifications` endpoint is expected to have a similar issue.
*   CORS errors are present but are a symptom of the failing Firestore queries.

# Day 17

## Feature Implementation: ML-driven Irrigation Prediction & Trigger

**Goal:** Implement a feature to display ML-based irrigation recommendations on the dashboard and allow users to manually trigger irrigation, leveraging existing sensor data generation and ML models.

**Summary of Changes:**

### Backend (`backend/`)

1.  **`backend/app/models/irrigation.py`**:
    *   Added `user_triggered: Optional[bool] = False` field to `IrrigationEventBase` and `IrrigationEvent` models to track if an irrigation event was manually initiated from the UI.

2.  **`backend/app/routes/irrigation.py`**:
    *   **Replaced `simulate_irrigation` endpoint with `POST /irrigation/trigger`**:
        *   This new endpoint handles requests to initiate an irrigation event.
        *   If `duration_minutes` is not provided in the request, it fetches the latest sensor data for the specified device using `sensor_service.get_latest_sensor_reading`.
        *   It then calls `ml_service.predict_irrigation_need` with this sensor data to determine the optimal irrigation duration.
        *   An `IrrigationEvent` is created and stored, recording the determined duration and the `user_triggered` status.
        *   Error handling is included for cases where sensor data is unavailable or ML prediction fails.
    *   **Updated `GET /irrigation/recommendations/{device_id}` endpoint**:
        *   Modified to fetch and use *actual* latest sensor data for the given `device_id` via `sensor_service.get_latest_sensor_reading` instead of using dummy data for ML predictions. This ensures recommendations are based on real-time conditions.

### Frontend (`Frontend/`)

1.  **`Frontend/src/views/DashboardView.vue`**:
    *   Introduced new reactive state variables: `currentDeviceId` (to track the device currently in focus), `irrigationRecommendation` (to store the ML prediction result), and `showIrrigationSpinner` (for UI feedback during API calls).
    *   Implemented `fetchIrrigationRecommendation()` method to call the backend's `GET /irrigation/recommendations/{device_id}` endpoint and update the `irrigationRecommendation` state.
    *   Implemented `triggerIrrigation()` method to call the backend's `POST /irrigation/trigger` endpoint when a user requests manual irrigation.
    *   Added logic within the `onMounted` lifecycle hook to automatically fetch the user's devices (selecting the first one as `currentDeviceId`) and then fetch the initial irrigation recommendation.
    *   Added new UI components within the template to display the fetched `irrigationRecommendation` (including prediction text, duration, and current conditions) and a "Trigger Irrigation Now" button.
    *   Ensured that `currentDeviceId` is passed as a prop to all dynamically rendered dashboard widgets (`<component :is="..." :device-id="currentDeviceId"></component>`) for device-specific data handling.

2.  **`Frontend/src/components/IrrigationControl.vue`**:
    *   Updated to accept a `deviceId` prop, making the component device-aware.
    *   Modified the `startIrrigation` method to integrate with the backend: it now sends an authenticated `POST` request to `/irrigation/trigger`, including the `deviceId`, selected `duration_minutes`, and `user_triggered: true`.
    *   Added a loading spinner to the "Start" button to provide visual feedback during the API call.

3.  **`Frontend/src/components/PredictionChart.vue`**:
    *   Updated to accept a `deviceId` prop, preparing it for potential future enhancements that might require device-specific historical or forecasting data.

**Current Status:**
The feature is fully implemented in terms of code changes on both the backend and frontend. Users can now view ML-driven irrigation recommendations and manually trigger irrigation events from the dashboard. The backend records these events and can use ML to determine durations.