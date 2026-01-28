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

### **Day 7: Backend Stability Fixes & Profile Picture Upload Setup**

**Accomplishments:**

*   **Resolved Backend `ImportError`s:**
    *   Fixed `ImportError: cannot import name 'db'` in `backend/app/services/alert_service.py` and `backend/app/services/notification_service.py` by correcting the import of `firebase_service.db`.
*   **Resolved Backend `NameError`:**
    *   Fixed `NameError: name 'Alert' is not defined` in `backend/app/services/alert_service.py` by re-inserting the missing `Alert` class definition and related Enums.
*   **Resolved Frontend Build Error:**
    *   Fixed `Rollup failed to resolve import "/path/to/default/profile_pic.png"` by creating a placeholder image at `Frontend/public/default_profile_pic.png` and updating the image path in `Frontend/src/views/ProfileView.vue` to `/default_profile_pic.png`.
*   **Backend - Profile Picture Upload Integration (Phase 1):**
    *   **Firebase Storage:** Integrated Firebase Storage into `backend/app/services/firebase_service.py`, including initializing the storage client, adding a mock storage client, and implementing an `upload_file_to_storage` method.
    *   **Configuration:** Added `FIREBASE_STORAGE_BUCKET` to `backend/app/config.py` for environment variable configuration.
    *   **API Endpoint:** Created a new `POST /users/{user_id}/upload-profile-picture` endpoint in `backend/app/routes/users.py` to handle file uploads, validation, and update the `profile_picture_url` in Firestore.
    *   **Frontend API Service:** Added `uploadProfilePicture` method to `Frontend/src/services/api.js` to communicate with the new backend upload endpoint.

**Current Issues & Next Steps:**

*   **Frontend - Profile Picture Upload UI:** The `Frontend/src/views/UpdateProfileView.vue` still needs to be updated to include the file input element and the logic to trigger the upload process. (Encountered a `replace` error during the last attempt).
*   **Firestore Index for Notifications:** The `GET /notifications/` endpoint requires a composite index to be created manually in Firebase for `user_id` and `created_at` fields. (User still needs to perform this step).
