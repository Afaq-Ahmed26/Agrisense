### **Day 4: Backend/Frontend Synchronization & Bugfixing**

**Accomplishments:**

*   **Fixed User Data Loading:** Successfully resolved the critical bug where the frontend was displaying "John Farmer" mock data instead of the actual logged-in user's information.
    *   **Root Cause:** Two-fold:
        1.  Incorrect route ordering in `backend/app/routes/users.py`, causing `GET /users/me` to be intercepted by a dynamic `/{user_id}` route.
        2.  Incorrect data types (`is_deleted` as string `"false"`, missing `updated_at`) in manually created Firestore user documents, and the `id` field not being populated from `doc.id` in the backend.
    *   **Fix:**
        1.  Reordered routes in `backend/app/routes/users.py` so `/users/me` is handled before `/{user_id}`.
        2.  Instructed user to update `is_deleted` to boolean `false` and add `updated_at` (timestamp) in Firestore.
        3.  Modified `backend/app/services/user_service.py` to explicitly set `id=doc.id` when creating the `User` Pydantic model from Firestore data.
    *   **Result:** Frontend now correctly displays logged-in user's profile and navigation bar details.

**Current Issues & Next Steps:**

1.  **Missing Firestore Index for User Listing:**
    *   **Problem:** Attempting to access the User Management page (which calls `GET /users/`) results in a `500 Internal Server Error` due to a missing Firestore composite index.
    *   **Status:** User has been provided with the link to create the necessary index in the Firebase Console.
    *   **Next Step:** User needs to create the index in Firestore.

2.  **New User Registration Failing (`422 Unprocessable Entity`):**
    *   **Problem:** Attempting to register a new user from the frontend results in a `POST /auth/register` returning a `422 Unprocessable Entity` status. Backend logs confirm that FastAPI's Pydantic validation is failing *before* the `register` function's custom logging is hit, indicating a mismatch in the structure or types of data being sent by the frontend compared to the `UserCreate` model expected by the backend.
    *   **Initial Analysis:** Frontend code in `Frontend/src/views/RegisterView.vue` appears to construct the `userData` object with the correct keys (`email`, `username`, `password`, `role`).
    *   **Next Step:** I will add more specific logging to the frontend (`Frontend/src/services/api.js`) to log the exact `userData` object *just before* it is sent to the backend. This will help us confirm the exact structure and values being transmitted.

### **Day 5: Registration Feature Refinement & Role Management Bugfix**

**Accomplishments:**

*   **Refined Registration Feature:**
    *   Initially removed the role selection dropdown from `Frontend/src/views/RegisterView.vue` to default all new registrations to a 'farmer' role for enhanced security.
    *   Re-implemented role selection in `Frontend/src/views/RegisterView.vue` to allow new users to register as either 'farmer' or 'officer', while explicitly preventing 'admin' signups from the frontend.

*   **Fixed User Role Update for Admins:**
    *   **Problem Identification:** Identified that admin users could not change other users' roles via the User Management interface (`Frontend/src/views/UserManagementView.vue`). The frontend `PATCH` request was being rejected by the backend, first with a `403 Forbidden` error and then a `500 Internal Server Error`.
    *   **Root Cause 1 (`403 Forbidden`):** The backend's `update_user` endpoint was incorrectly expecting the user's role to be present in the JWT payload, which only contains basic Firebase Auth information, not custom Firestore roles.
    *   **Fix 1:** Modified `backend/app/routes/users.py` to fetch the acting user's full profile (including `role`) from Firestore based on their UID from the JWT before performing authorization checks.
    *   **Root Cause 2 (`500 Internal Server Error` - `AttributeError`):** The `update_user` endpoint attempted to access `user_update.password`, but the `UserUpdate` Pydantic model (`backend/app/models/user.py`) did not include a `password` field.
    *   **Fix 2:** Added `password: Optional[str] = None` to the `UserUpdate` model in `backend/app/models/user.py` to align the model with the endpoint's logic.
    *   **Fix 3:** Changed `@router.put` to `@router.patch` in `backend/app/routes/users.py` for the `update_user` endpoint to correctly handle `PATCH` requests from the frontend.
    *   **Result:** Admin users can now successfully update other users' roles and other profile details.

**Current Issues & Next Steps:**

*   Continue monitoring for any further issues related to user management and roles.
*   Ensure the overall system stability after these changes.

### **Day 6: Core Feature Enhancements - Phase 1**

**Accomplishments:**

*   **Implemented In-App Notification Center:**
    *   **Backend:** Created `Notification` model (`backend/app/models/notification.py`), `notification_service.py` for logic, and `notifications.py` for API routes. Integrated notification creation into `alert_service.py` to generate notifications when alerts occur. Fixed `firebase_service` import error in `alert_service.py`.
    *   **Frontend:** Developed `NotificationsView.vue` to display notifications, added `/notifications` route in `router.js`, integrated `getNotifications` and `markNotificationAsRead` into `api.js`, and added a navigation link in `App.vue`.

*   **Implemented Enhanced User Profile:**
    *   **Backend:** Extended `UserBase`, `UserUpdate`, and `User` models in `backend/app/models/user.py` to include `full_name`, `location`, and `profile_picture_url`. Updated `update_user` endpoint in `backend/app/routes/users.py` to correctly persist these new fields to Firestore.
    *   **Frontend:** Modified `ProfileView.vue` to display the new user details. Updated `UpdateProfileView.vue` to include form fields for editing `full_name`, `location`, and `profile_picture_url`.

*   **Implemented Dashboard Customization:**
    *   **Backend:** Added `dashboard_preferences: Optional[Dict]` to `UserBase`, `UserUpdate`, and `User` models in `backend/app/models/user.py`. Updated `update_user` endpoint in `backend/app/routes/users.py` to persist `dashboard_preferences` to Firestore.
    *   **Frontend:** Modified `DashboardView.vue` to dynamically render widgets based on `dashboard_preferences`. Implemented logic to fetch, display, and save dashboard layouts, including a "Customize Dashboard" toggle and save functionality.

**Next Steps:**

*   **Phase 2 Features:** Proceed with implementing the next set of desired features.
*   **Refinement:** Implement advanced UI/UX for dashboard customization (e.g., drag-and-drop, widget visibility toggles).
*   **Testing:** Thoroughly test the newly implemented features for robustness and correctness.

### **Day 7: Feature Refinements, Bug Fixes, and Activity Logging Implementation**

**Accomplishments:**

*   **Resolved Backend `ImportError`s:**
    *   Fixed `ImportError: cannot import name 'db'` in `backend/app/services/alert_service.py` and `backend/app/services/notification_service.py` by correcting the import of `firebase_service.db`.
*   **Resolved Backend `NameError`:**
    *   Fixed `NameError: name 'Alert' is not defined` in `backend/app/services/alert_service.py` by re-inserting the missing `Alert` class definition and related Enums.
*   **Resolved Frontend Build Error:**
    *   Fixed `Rollup failed to resolve import "/path/to/default/profile_pic.png"` by creating a placeholder image at `Frontend/public/default_profile_pic.png` and updating the image path in `Frontend/src/views/ProfileView.vue` to `/default_profile_pic.png`.
*   **Removed Profile Picture Feature:**
    *   Completely removed profile picture upload and display functionality from both frontend and backend to eliminate Firebase Storage dependency and simplify the application. This involved removing endpoints, model fields, service logic, and UI components.
*   **Improved User Role Management UI:**
    *   Replaced the `prompt()`-based role change with an interactive inline dropdown menu in `Frontend/src/views/UserManagementView.vue`, including a loading spinner for visual feedback.
*   **Enhanced In-App Notifications UI:**
    *   Created `notificationsStore` (`Frontend/src/store/notifications.js`) for centralized notification state management.
    *   Integrated a dynamic notification bell icon with an unread count badge into the main navigation bar (`Frontend/src/App.vue`), implementing periodic polling for new notifications.
    *   Refactored `Frontend/src/views/NotificationsView.vue` to utilize the centralized store.
*   **Implemented Activity Logging/Audit Trail:**
    *   **Backend:**
        *   Created `backend/app/models/activity_log.py` for the `ActivityLog` Pydantic model.
        *   Created `backend/app/services/activity_log_service.py` with functions to log and retrieve activities.
        *   Integrated `log_activity` into `backend/app/routes/auth.py` (user login), `backend/app/routes/users.py` (user role changes), and `backend/app/routes/alerts.py` (alert acknowledgments/resolutions).
        *   Created `backend/app/routes/activity_logs.py` with an admin-only endpoint to fetch logs.
        *   Included the new `activity_logs` router in `backend/app/main.py`.
    *   **Frontend:**
        *   Added `getActivityLogs` function to `Frontend/src/services/api.js`.
        *   Created `Frontend/src/views/ActivityLogView.vue` to display logs in a table.
        *   Added an admin-only navigation link for "Activity Log" in `Frontend/src/App.vue`.
        *   Added a route for `/activity-logs` in `Frontend/src/router.js`, protected for admin access.
*   **Fixed Backend `SyntaxError`:**
    *   Corrected parameter order in `backend/app/routes/activity_logs.py` to resolve `SyntaxError: parameter without a default follows parameter with a default`.

**Current Issues & Next Steps:**

*   **Firestore Index for Notifications:** The `GET /notifications/` endpoint requires a composite index to be created manually in Firebase for `user_id` (Ascending) and `created_at` (Descending). (User still needs to perform this step to fully enable notifications).
*   **Firestore Index for User Listing:** The `GET /users/` endpoint requires a composite index to be created manually in Firebase for `created_at` (Ascending) and `is_deleted` (Ascending). (User still needs to perform this step to fully enable user listing).

---

### **Future Plans (Features to Add without Hardware/ML Integration)**

Here are some feature suggestions that will add significant value and interactivity to your AgriSense application, leveraging your existing Firebase and frontend/backend setup, without requiring external hardware integrations or a deployed ML model yet:

**Core Functionality & UX Enhancements:**

1.  **Enhanced User Profile Management (Beyond Basics):**
    *   **User Preferences:** Allow users to configure personal settings like preferred units (e.g., Celsius/Fahrenheit, liters/gallons), time zone, or notification sound preferences. Store these in Firestore.
    *   **Account Activity Log (Improved Display):** Enhance the Activity Log with filtering, pagination, and search capabilities.

2.  **Advanced Notification & Alert System:**
    *   **Configurable Alert Thresholds (Admin/Officer):** Implement UI for setting custom alert thresholds for simulated sensor data (e.g., "notify me if temperature goes above 30°C"). These thresholds would be stored in Firestore and checked by your backend against simulated data.
    *   **Notification Preferences:** Allow users to specify *how* they want to receive certain notifications (e.g., in-app only, email for critical alerts).
    *   **Notification Archiving/Filtering:** Enable users to archive old notifications or filter them by type (e.g., "show only critical alerts").

3.  **Role-Based Access Control (RBAC) Fine-Tuning:**
    *   **Permission Management (Admin Feature):** While roles are set, an admin UI to view or even modify specific permissions associated with each role (e.g., "Officer can view reports but not manage users"

### **Day 12: Advanced Features Implementation & Bugfixing**

**Accomplishments:**

*   **Implemented Enhanced User Profile Management (User Preferences):**
    *   Developed a backend model and API endpoints for user-specific preferences (e.g., temperature unit, volume unit, time zone).
    *   Integrated a new section into the `ProfileView.vue` frontend component, allowing users to view and update their personal settings.

*   **Implemented Configurable Alert Thresholds:**
    *   Created a backend model (`AlertThresholds`) and corresponding API endpoints (`/thresholds`) for setting system-wide alert thresholds for sensor data (temperature, humidity, soil moisture).
    *   Implemented role-based access control to ensure only 'admin' or 'officer' roles can manage these thresholds.
    *   Modified the `AlertService` to dynamically fetch and apply these configurable thresholds from Firestore instead of using hardcoded values.
    *   Developed a new admin-only frontend view (`Frontend/src/views/Admin/ThresholdsView.vue`) for managing these settings, protected by router guards.

*   **Implemented Notification Preferences:**
    *   Introduced a backend model (`NotificationPreferences`) and API endpoints (`/users/{user_id}/notification-preferences`) allowing users to define their preferred notification channels (in-app, email, or none) for different alert severities (critical, high, medium, low).
    *   Updated the `AlertService` to consult these user-specific preferences before dispatching notifications.
    *   Integrated a notification preferences management section into the `ProfileView.vue` frontend component.

*   **Implemented Account Activity Log Enhancements:**
    *   Enhanced the backend API for activity logs (`/activity-logs`) to support advanced querying, including pagination (`skip`, `limit`) and filtering by `user_id` and `action`.
    *   Refactored the `ActivityLogView.vue` frontend component to incorporate UI elements for pagination (Next/Previous), user filtering, and action filtering, providing a more robust audit trail.

*   **Implemented Notification Archiving/Filtering:**
    *   Updated the `Notification` data model to include an `is_archived` field.
    *   Extended the backend API (`/notifications`) to allow filtering notifications by their archive status and added dedicated endpoints for archiving (`/notifications/{notification_id}/archive`) and unarchiving (`/notifications/{notification_id}/unarchive`) notifications.
    *   Modified the `notificationsStore` (Vuex) and `NotificationsView.vue` frontend component to provide a user interface for filtering notifications (active/archived), and actions to archive or unarchive individual notifications, along with pagination.

**Errors Encountered and Resolved:**

*   **`NameError: name 'Optional' is not defined` in `backend/app/services/notification_service.py`:**
    *   **Cause:** The `Optional` type hint was used without being imported from the `typing` module.
    *   **Resolution:** Added `from typing import Optional, List` to the file.
*   **`NameError: name 'Optional' is not defined` in `backend/app/routes/activity_logs.py`:**
    *   **Cause:** Similar to the above, `Optional` was used without being imported.
    *   **Resolution:** Added `from typing import List, Optional` to the file.
*   **`bash: line 1: python: command not found`:**
    *   **Cause:** The `python` executable was not directly accessible in the shell's PATH without explicit virtual environment activation.
    *   **Resolution:** Instructed to use explicit virtual environment activation in the command: `source venv/bin/activate && python start_server.py`.
*   **`[Errno 98] address already in use` on port 8000:**
    *   **Cause:** A previous instance of the server or another process was already listening on port 8000.
    *   **Resolution:** Identified and terminated the conflicting process using `lsof -i :8000` and `kill -9 <PID>`.

**Current Status:**

*   All requested features outlined in "Future Plans" (User Preferences, Configurable Alert Thresholds, Notification Preferences, Activity Log Enhancements, Notification Archiving/Filtering) have been successfully implemented in both the backend and frontend.
*   The backend server is now starting and running without compilation errors.
*   A potential "failed to fetch" error when filtering the Activity Log is pending further investigation and user input. It is highly suspected to be due to missing Firestore composite indexes, which the user will need to create manually.

---

### **Day 13: Preferences Feature Enhancement & Bugfix**

**Accomplishments:**

*   **Fixed User Preferences Not Reflecting on Dashboard:**
    *   **Problem Identified:** Users reported that changing unit preferences (e.g., liters to gallons, Celsius to Fahrenheit) in the Profile view did not affect the dashboard display. Components were showing hardcoded units instead of using user preferences.
    *   **Root Cause:** Dashboard components (`SensorDisplay.vue`, `PredictionChart.vue`, `LogsTable.vue`) were not retrieving or applying user preferences when formatting data for display.
    *   **Solution Implemented:**
        *   Created a new utility file `Frontend/src/utils/unitConverter.js` with functions for converting between different units based on user preferences (temperature: Celsius/Fahrenheit/Kelvin, volume: liters/gallons/milliliters).
        *   Updated `SensorDisplay.vue` to use user preferences for temperature unit display.
        *   Updated `PredictionChart.vue` to use user preferences for volume unit display in charts and tooltips.
        *   Updated `LogsTable.vue` to use user preferences for both temperature and volume unit display in the irrigation history table.
        *   Enhanced `ProfileView.vue` to refresh user data in the auth store after saving preferences, ensuring other components pick up the changes immediately.
        *   Added functions to `IrrigationControl.vue` to format volumes with user preferences (future-proofing for when volume units are displayed).

*   **Improved Component Architecture:**
    *   Made dashboard components reactive to preference changes by properly accessing user preferences from the auth store.
    *   Ensured consistent unit formatting across all dashboard components.
    *   Maintained backward compatibility for users who haven't set preferences yet (defaults to Celsius and liters).

**Current Status:**

*   The preferences feature now works as intended - when users change their unit preferences in the Profile view, the dashboard components immediately reflect those changes.
*   All dashboard components now properly use user preferences for unit formatting.
*   The system maintains backward compatibility with default units for users who haven't customized their preferences.
*   The user experience is now consistent across the application with respect to unit preferences.

---

### **Day 30: ESP32 Integration and Backend Communication**

**Accomplishments:**

*   **DHT Sensor Correction:** Updated the ESP32 firmware (`AgriSense_ESP32.ino`) to correctly use the DHT22 sensor, as specified by the user.
*   **Temporary API Authentication Bypass:** Modified the backend (`backend/app/routes/sensors.py`) to temporarily remove the JWT authentication requirement for the `create_sensor_reading` endpoint. This allows the ESP32 to post data directly for initial testing without complex device authentication.
*   **ESP32 Network Integration:** Implemented Wi-Fi connectivity and HTTP POST request logic in `AgriSense_ESP32.ino`. The ESP32 now:
    *   Connects to the user-provided Wi-Fi network (`Agrisense`, password `passwordd`).
    *   Automatically generates a unique device ID based on its MAC address (e.g., `esp32-XXXXXX`).
    *   Collects sensor data (soil moisture, temperature, humidity, light level).
    *   Constructs a JSON payload with the sensor data.
    *   Sends this data via an HTTP POST request to the backend's `/api/sensors/{device_id}/readings` endpoint.
*   **User Guidance for Setup:** Provided instructions for the user on:
    *   How to find their computer's local IP address (to configure `API_BASE_URL` in the ESP32 code).
    *   The necessity of restarting the backend server after the authentication change.
    *   How to install the `DHT sensor library` in the Arduino IDE to resolve compilation errors.

**Current Issues & Next Steps:**

*   **Verification:** The user needs to:
    1.  Restart the backend server.
    2.  Update the `API_BASE_URL` in `AgriSense_ESP32.ino` with their computer's actual IP address.
    3.  Upload the updated code to the ESP32.
    4.  Monitor the Serial Monitor and backend logs to confirm data is being sent and received successfully.
    5.  Verify if sensor readings are visible on the frontend dashboard.
*   **Security Re-implementation:** Once data flow is confirmed, the temporary authentication bypass in the backend will need to be replaced with a secure device authentication method (e.g., API keys).
### **Day 69: Real-time Sensor Data Display & Hardware Debugging**

**Accomplishments:**

*   **Database Clarification:** Confirmed the project exclusively uses Google Cloud Firestore for data persistence, clarifying its differences and advantages over Firebase Realtime Database for this application.
*   **Frontend-Backend Integration for Live Sensor Data:**
    *   **Analyzed Architecture:** Reviewed `HW_code.ino`, backend API endpoints (`backend/app/routes/sensors.py`), backend services (`backend/app/services/sensor_service.py`), and frontend components (`Frontend/src/views/DashboardView.vue`, `Frontend/src/services/api.js`).
    *   **API Service Update:** Modified `Frontend/src/services/api.js` to correctly utilize the dedicated backend endpoint `/sensors/{device_id}/latest-reading` for fetching the most recent sensor data.
    *   **Dashboard Refactoring:** Refactored `Frontend/src/views/DashboardView.vue` to:
        *   Remove direct Firestore subscription logic for sensor data.
        *   Implement an API polling mechanism using `setInterval` to fetch live sensor data from the FastAPI backend every 5 seconds.
        *   Ensured proper cleanup of the polling interval on component unmount.
*   **Hardware Debugging for ESP32/Sensor Stability:**
    *   **Problem Identification:** User reported `ets Jul 29 2019 12:21:46 rst:0x7 (TG0WDT_SYS_RESET)` (Watchdog Timer reset) and `[BH1750] ERROR: other error` when the soil moisture sensor was connected, indicating hardware instability and conflicts.
    *   **Root Cause:** The soil moisture sensor, when continuously powered, was causing electrical interference or power issues, leading to I2C bus instability (affecting BH1750) and ultimately ESP32 crashes.
    *   **Solution Implemented in `HW_code.ino`:**
        *   Removed the temporarily hardcoded soil moisture value.
        *   Renamed `SOIL_MOISTURE_PIN` to `SOIL_MOISTURE_SIGNAL_PIN` for clarity.
        *   Introduced `SOIL_MOISTURE_POWER_PIN` (GPIO16) to switch power to the soil moisture sensor on/off only when a reading is taken. This significantly improved power stability and prevented interference.
        *   Added small `delay(100)` calls after DHT and BH1750 initializations in `setup()` for stabilization.
        *   Added more verbose debug output to `sendSensorData()` to explicitly report Firebase readiness and interval status.
    *   **User Confirmation:** The user confirmed that the ESP32 is now booting and running stably with the soil moisture sensor connected, and `setup()` completes without errors or crashes.

**Current Status:**

*   The frontend is configured to poll the backend for live sensor data, aligning with the project's central backend architecture.
*   The ESP32 is now stable and expected to be successfully sending sensor data to Firestore.

**Next Steps:**

*   **Firebase Data Verification:** User needs to confirm that sensor data is appearing correctly in their Firebase Console's Firestore `devices/<DEVICE_ID>/readings` collection.
*   **Frontend Display Verification:** Once data is confirmed in Firestore, verify that the frontend dashboard (`SensorDisplay` component) is correctly displaying these live values.
---

### **Day 98: Hardware Integration, Production Optimization & Quota Management**

**Accomplishments:**

*   **Production Readiness & Hardware Integration:**
    *   **Full-Stack Alignment:** Synchronized the ESP32 firmware, FastAPI backend, and Vue.js frontend to work with actual hardware on the local network (`192.168.100.253`).
    *   **Fixed Device ID:** Hardcoded the device ID to `esp32-b47cb8` across the hardware and mock-seeding logic to ensure immediate "plug-and-play" functionality for the user's specific ESP32 module.
    *   **Backend Connectivity:** Verified that the backend correctly listens on `0.0.0.0:8000`, allowing the ESP32 and other network devices to post sensor data.

*   **Firebase Quota Optimization (The "65K Reads" Fix):**
    *   **Identified Root Cause:** Determined that high-frequency polling (5s) combined with unoptimized backend logic was causing a massive spike in Firestore reads (65,000 reads in 2 hours).
    *   **Implemented Backend Caching:** Added an in-memory caching layer to `AlertService` (`backend/app/services/alert_service.py`) for device owners and user preferences. This eliminates up to 3 redundant Firestore reads for every incoming sensor heartbeat.
    *   **Optimized Hardware Throttling:** Increased the ESP32 sensor read interval (`SENSOR_READ_INTERVAL_MS`) from 5 seconds to **10 seconds** for the demo, significantly reducing write operations while maintaining responsiveness.
    *   **Frontend Polling Optimization:** Updated `DashboardView.vue` to poll every 10 seconds and implemented a visibility check (`document.hidden`) to stop all background reads when the browser tab is not active.

*   **System Stabilization:**
    *   **Mock/Prod Toggle:** Successfully navigated a Firestore "Quota Exceeded" event by implementing a temporary mock-seeding mechanism to allow development to continue, then reverted to production settings once optimizations were in place.
    *   **CORS Fix:** Updated `backend/app/main.py` to allow wildcard origins and properly handle credentials for local network development.

**Current Status:**

*   **Phase 1 Complete:** The system is fully integrated with physical hardware. All four sensors (Temperature, Humidity, Soil Moisture, Light Level) are reporting live data to the dashboard.
*   **Demo Ready:** The system is tuned for a "Plant Pot Demo" with a 10-second refresh rate, providing a balance between real-time feedback and Firebase quota safety.
*   **ML Status:** Machine Learning auto-triggers remain disabled to ensure Phase 1 stability and minimize API complexity during initial hardware testing.

**Next Steps:**

*   **Hardware Validation:** User to confirm live data updates on the dashboard after watering the plant (expecting a ~10s response time).
*   **Monitor Quota:** Observe the Firebase Console to verify that the new caching and throttling logic has successfully stabilized the read/write counts.
*   **Phase 2 Planning:** Prepare for re-enabling ML recommendations and automated irrigation triggers once sensor stability is confirmed.
