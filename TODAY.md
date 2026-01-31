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
    *   **Permission Management (Admin Feature):** While roles are set, an admin UI to view or even modify specific permissions associated with each role (e.g., "Officer can view reports but not manage users"). This is more granular than just assigning roles.

4.  **Reporting & Data Visualization (More Dynamic):**
    *   **Custom Date Range Selector:** Enhance existing reports to allow users to select arbitrary date ranges (e.g., "show data from last Tuesday to yesterday").
    *   **Comparison Views:** Allow users to compare data from different sensors or different time periods side-by-side on charts.
    *   **Data Export:** Implement functionality to export displayed sensor data or reports to CSV or PDF format (frontend-driven generation).

**Preparing for ML & Hardware (UI/UX Placeholders):**

5.  **"Connect Device" Walkthrough (Placeholder):**
    *   Create a UI flow for "adding a new device" where users can input a simulated device ID, type, and location. Even if it's just mock data for now, this prepares the application for real hardware integration later.
    *   Show a "Device Status: Offline (Simulated)" for these placeholders.

6.  **Mock ML Prediction Visualization:**
    *   Since you don't have an ML model yet, you could generate *mock* predictions (e.g., random numbers, simple linear trends) and display them in a chart or a dedicated "ML Insights" section. This showcases what the feature *will* look like and helps in designing the UI for real ML outputs.

**Security & Maintainability:**

7.  **User Impersonation (Admin Feature):** Allow admins to securely "impersonate" another user's session to troubleshoot issues or provide support. (Requires careful security considerations).

### Day 9: ML Model Integration, Feature Enhancements, and Bug Squashing

**Summary:**
Today's session focused on the end-to-end integration of the machine learning model for irrigation prediction. This involved debugging complex dependency issues, retraining the model for compatibility, and updating the full application stack (backend, frontend) to support the new feature. We also implemented several UI/UX improvements and bug fixes related to user management.

**Errors & Resolutions:**

1.  **`numpy` CPU Incompatibility:**
    *   **Error:** `RuntimeError: NumPy was built with baseline optimizations (X86_V2) but your machine doesn't support it.`
    *   **Cause:** The version of `numpy` installed was compiled for a more modern CPU.
    *   **Resolution:** After several attempts to rebuild from source, the issue was resolved by downgrading `pandas` and `scikit-learn` to versions that use an older, more broadly compatible `numpy` version (`1.26.4`).

2.  **`scikit-learn` Model Incompatibility:**
    *   **Error:** `_pickle.UnpicklingError: STACK_GLOBAL requires str` and an `InconsistentVersionWarning`.
    *   **Cause:** The provided `irrigation_model.pkl` was created with a newer version of `scikit-learn` (`1.6.1`) than could be run in the user's environment, making the model file unreadable.
    *   **Resolution:** Created a `model/train_model.py` script based on the provided Jupyter Notebook. This script was used to retrain the model, generating a new `irrigation_model.pkl` that is 100% compatible with the user's current environment.

3.  **User Management Bugs:**
    *   **"Admin" Role Missing:** Admins could not assign the "Admin" role to other users. This was fixed by conditionally rendering the "Admin" option in the `UserManagementView.vue` dropdown, visible only to logged-in admins.
    *   **Admin Not Visible in List:** The admin's own account was hidden from the user list. This was changed to show all users, but with modification controls disabled for the admin's own row to prevent accidental self-lockout.
    *   **"Inactive" Status Bug:** All users incorrectly showed as "Inactive". This was fixed by adding an `is_active` field to the backend User model (defaulting to `True`) and updating the user modification endpoint to handle status changes.

**Accomplishments:**

*   **Successfully Integrated ML Model:** The backend now uses a compatible, retrained `RandomForestRegressor` model to predict irrigation valve duration.
*   **Full-Stack Feature: Light Sensor:**
    *   Added `light_level` to the backend sensor model, simulation service, and ML prediction endpoint.
    *   Added a "Light Level" display card to the frontend dashboard.
*   **Enhanced User Management:** The user management panel is now more robust and functions as per the admin's requirements.
*   **Resolved Critical Bugs:** Fixed the user status display and several complex dependency and model versioning issues.

### Day 10: Dashboard UI & Data Management Improvements

**Summary:**
Today's session focused on resolving a persistent blank dashboard issue and enhancing the application's data management and UI capabilities. This involved debugging frontend rendering logic, configuring Firebase security rules, implementing new UI features, and expanding backend data models.

**Accomplishments:**

*   **Resolved Blank Dashboard Issue:**
    *   Diagnosed and resolved the `permission-denied` error from Firebase Firestore by guiding the user to configure appropriate security rules, allowing the frontend to access necessary data.
    *   Fixed a `ReferenceError: clearTimers is not defined` in `Frontend/src/components/IrrigationControl.vue`, which was caused by an accidental revert to an older script version.
    *   Temporarily disabled `vue-draggable-next` in `Frontend/src/views/DashboardView.vue` to confirm that dashboard widgets render correctly with a standard `v-for` loop, thereby isolating the issue to the `draggable` component's integration.
*   **Expanded Activity Logging:**
    *   Implemented detailed activity logging in the backend for user login, logout, and profile updates, providing a more comprehensive audit trail.
    *   Modified `backend/app/routes/auth.py` and `backend/app/routes/users.py` to record these actions using the `log_activity` service.
*   **Enhanced Irrigation History with Sensor Data:**
    *   Modified the `IrrigationEvent` model in `backend/app/models/irrigation.py` to include fields for `temperature`, `humidity`, `soil_moisture`, and `light_level`.
    *   Updated the `simulate_irrigation` endpoint in `backend/app/routes/irrigation.py` to generate and store dummy sensor data alongside irrigation events.
    *   Implemented `create_irrigation_event_in_firestore` and `get_irrigation_events_from_firestore` functions in `backend/app/services/firebase_service.py` to persist and retrieve irrigation events with sensor data.
    *   Updated `Frontend/src/components/LogsTable.vue` to display and export the new sensor data columns, enhancing the utility of irrigation logs for potential ML model retraining.
*   **Implemented "Connect Device" UI Flow:**
    *   Created `Frontend/src/views/ConnectDeviceView.vue` to provide a user interface for adding new simulated devices, including input fields for ID, type, and location, and displaying a simulated "offline" status.
    *   Integrated the "Connect Device" view into the frontend navigation and routing.
*   **Implemented "Customize Dashboard" Feature (Core Logic):**
    *   Integrated `vue-draggable-next` into `Frontend/src/views/DashboardView.vue` to enable drag-and-drop functionality for dashboard widgets.
    *   Added controls to hide and show widgets, with user preferences stored in Firebase.

**Current Issues & Next Steps:**

*   **`vue-draggable-next` Integration Debugging:** The `draggable` component, when re-integrated into `DashboardView.vue`, still results in a blank dashboard. Further investigation is required to correctly integrate `vue-draggable-next` to allow drag-and-drop functionality while maintaining dashboard visibility. This might involve adjusting the structure of the items passed to `draggable` or exploring alternative integration patterns.
*   **Dashboard Widget Prioritization:** Implement dynamic positioning of the `AlertsBanner` (top priority if active) and other dashboard widgets based on user preferences and alert status, as per user suggestion. This requires refining the `dashboardLayout` logic in `DashboardView.vue`.
*   **Frontend UI Cleanup:** Remove debugging `console.log` statements from `Frontend/src/views/DashboardView.vue`.