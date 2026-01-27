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