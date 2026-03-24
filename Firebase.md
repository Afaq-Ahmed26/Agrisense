# Firebase Integration Plan for Agriscense

This document outlines the plan for integrating Firebase into the Agriscense project, focusing on features that do not require hardware interaction or machine learning models. The primary goal is to leverage Firebase Authentication for user management and potentially Firestore for certain data storage needs.

## Why Firebase?

Firebase offers a robust, scalable, and easy-to-integrate platform for various backend services, including:
-   **Authentication:** Secure user registration, login, and session management.
-   **Firestore:** NoSQL cloud database for flexible data storage and real-time synchronization.
-   **Cloud Functions:** Serverless backend logic (can be considered later if needed).

## Scope of Initial Integration (Without Hardware/ML)

The initial integration will focus on:
1.  **User Authentication:** Replacing or augmenting the current authentication system with Firebase Auth for user registration, login, and session management. This directly addresses the instability mentioned in `TODAY.md` regarding login/logout.
2.  **User Profile Storage:** Storing basic user profile information in Firestore or using Firebase Auth's built-in profile features.

## What YOU (the User) Need to Do

These are critical setup steps that require access to the Google Cloud Console and Firebase Console.

1.  **Create a Firebase Project:**
    *   Go to the [Firebase Console](https://console.firebase.google.com/).
    *   Click "Add project" and follow the prompts to create a new project for Agriscense.

2.  **Enable Firebase Authentication:**
    *   In your Firebase project, navigate to "Authentication" -> "Sign-in method."
    *   Enable the **Email/Password** provider. You may also consider enabling other providers like Google Sign-In if desired, but start with Email/Password.

3.  **Enable Firestore Database:**
    *   In your Firebase project, navigate to "Firestore Database."
    *   Click "Create database." Choose "Start in production mode" (you can adjust security rules later).
    *   Select a Cloud Firestore location (e.g., `nam5 (us-central)`).

4.  **Get Web App Configuration:**
    *   In your Firebase project settings (Project overview -> Project settings, click the "</>" web icon under "Your apps").
    *   Register your web app and copy the Firebase configuration object. This JavaScript object contains your API key, project ID, etc. **You will need to provide this to me.**

5.  **Generate Firebase Admin SDK Service Account Key (for Backend):**
    *   In your Firebase project settings, navigate to "Service accounts."
    *   Click "Generate new private key" and then "Generate key."
    *   A JSON file will be downloaded. This file contains the credentials for your backend to interact with Firebase Admin SDK. **You will need to provide the contents of this file to me securely.**

6.  **Securely Provide Credentials:**
    *   For the web app configuration (Step 4), you can provide the JSON directly in our chat, or ideally, add it to your frontend's environment variables (`.env`).
    *   For the service account key (Step 5), the most secure way is to put the contents of the JSON file into an environment variable in your backend (e.g., `FIREBASE_ADMIN_SDK_CONFIG`) or ensure the JSON file is accessible but **NOT committed to version control**.

## What I (the Agent) Can Do

Once you have completed the setup steps and provided the necessary configuration/credentials, I can proceed with the following implementations:

### Frontend (`Frontend/`)

1.  **Install Firebase SDK:**
    *   Run `npm install firebase` in the `Frontend/` directory.
2.  **Initialize Firebase:**
    *   Create `Frontend/src/services/firebaseConfig.js` to store the Firebase web app configuration and initialize the Firebase app.
    *   Update `Frontend/src/main.js` to import and initialize Firebase.
3.  **Refactor Authentication Service:**
    *   Modify `Frontend/src/services/auth.js` to use Firebase Authentication for user registration (`createUserWithEmailAndPassword`), login (`signInWithEmailAndPassword`), and logout (`signOut`).
    *   Implement logic to handle Firebase user objects and update the Vuex store (`Frontend/src/store/auth.js`) accordingly.
4.  **Update UI Components:**
    *   Adjust `Frontend/src/views/LoginView.vue` and `Frontend/src/views/RegisterView.vue` to interact with the new Firebase-based `auth.js` service.
    *   Update `Frontend/src/views/ProfileView.vue` and potentially `Frontend/src/views/UpdateProfileView.vue` to display and manage Firebase user profile information (e.g., display name, email).
    *   Modify `Frontend/src/router.js` to implement Firebase Auth state observers and potentially route guards to protect authenticated routes.

### Backend (`backend/`)

1.  **Install Firebase Admin SDK:**
    *   Run `pip install firebase-admin` in the `backend/` directory or add it to `requirements.txt`.
2.  **Initialize Firebase Admin SDK:**
    *   Update `backend/app/services/firebase_service.py` to initialize the Firebase Admin SDK using the service account credentials you provide.
3.  **Implement Firebase ID Token Verification:**
    *   Modify `backend/app/middleware/auth.py` to intercept incoming requests, extract the Firebase ID token from the Authorization header, and verify it using the Firebase Admin SDK.
    *   Attach the authenticated Firebase user's UID and claims to the request context.
4.  **Update User Routes and Services:**
    *   Adjust `backend/app/routes/users.py` and `backend/app/services/auth_service.py` to rely on the verified Firebase UID for user identification and authorization, rather than an internal JWT or session system.
    *   If user profiles are stored in Firestore, `backend/app/routes/users.py` might interact with `firebase_service.py` to read/write user data to Firestore.

---

**Next Steps:**

Please proceed with the "What YOU (the User) Need to Do" section. Once you have completed those steps and are ready, provide the Firebase web app configuration and the service account key contents (securely, as described in step 6) so I can begin the implementation.