# Firebase Integration Guide for AgriSense Frontend

This guide outlines the steps to integrate Firebase into your AgriSense Vue.js frontend application. The project already includes the `firebase` npm package and placeholders for Firebase configuration, making the integration process streamlined.

---

## 1. Firebase Project Setup (External to this Project)

Before proceeding with code changes, you need to set up your Firebase project in the Firebase Console.

1.  **Create a Firebase Project:**
    *   Go to the [Firebase Console](https://console.firebase.google.com/).
    *   Click "Add project" and follow the on-screen instructions to create a new project.

2.  **Register Your Web App:**
    *   Once your project is created, click the "Web" icon (</>) to add Firebase to your web app.
    *   Follow the setup steps. You will be given your Firebase configuration object. This is crucial for your `.env` file.

3.  **Enable Firebase Services:**
    *   **Authentication:** In the Firebase Console, navigate to "Authentication" (under "Build") and enable the "Email/Password" sign-in method (and any other methods you plan to use).
    *   **Firestore Database:** Navigate to "Firestore Database" (under "Build"). Click "Create database" and choose "Start in production mode" (you can adjust security rules later). Select a location for your database.
    *   **(Optional) Realtime Database:** If you prefer Realtime Database over Firestore for some data, enable it similarly. Firestore is generally recommended for new projects.

4.  **Configure Environment Variables (`.env` file):**
    *   Your project uses `import.meta.env` for environment variables, which is typical for Vite projects. The `src/config.js` file already has placeholders for Firebase credentials.
    *   In the root of your `Frontend` directory, ensure you have a `.env` file (as mentioned in `README.md`).
    *   Populate it with your actual Firebase configuration values obtained from step 2.
    *   **Important:** All variables used with `import.meta.env` in Vite must be prefixed with `VITE_`.

    ```dotenv
    # Example .env file (replace with your actual values)
    VITE_FIREBASE_API_KEY="YOUR_API_KEY"
    VITE_FIREBASE_AUTH_DOMAIN="YOUR_PROJECT_ID.firebaseapp.com"
    VITE_FIREBASE_PROJECT_ID="YOUR_PROJECT_ID"
    VITE_FIREBASE_STORAGE_BUCKET="YOUR_PROJECT_ID.appspot.com"
    VITE_FIREBASE_MESSAGING_SENDER_ID="YOUR_MESSAGING_SENDER_ID"
    VITE_FIREBASE_APP_ID="YOUR_APP_ID"
    VITE_FIREBASE_MEASUREMENT_ID="YOUR_MEASUREMENT_ID"

    # Keep your existing API base URL if you're using a hybrid approach
    VITE_API_BASE_URL="http://localhost:8000/api/v1"
    ```

---

## 2. Create and Initialize Firebase Service (`src/services/firebase.js`)

You need to create a new file to centralize your Firebase initialization and exports.

1.  **Create `src/services/firebase.js`:**
    Create a new file at `src/services/firebase.js`.

2.  **Add Initialization Code:**
    Add the following content to `src/services/firebase.js`:

    ```javascript
    // src/services/firebase.js
    import { initializeApp } from 'firebase/app';
    import { getAuth } from 'firebase/auth';
    import { getFirestore } from 'firebase/firestore';
    // If you plan to use Realtime Database instead of Firestore, uncomment the line below:
    // import { getDatabase } from 'firebase/database';

    import { CONFIG } from '@/config';

    // Firebase configuration from src/config.js
    const firebaseConfig = CONFIG.FIREBASE_CONFIG;

    // Initialize Firebase
    const app = initializeApp(firebaseConfig);

    // Initialize Firebase services
    const auth = getAuth(app);
    const db = getFirestore(app);
    // If you use Realtime Database:
    // const rtdb = getDatabase(app);

    // Export the initialized services
    export {
      app,
      auth,
      db,
      // rtdb // Uncomment if using Realtime Database
    };
    ```

---

## 3. Integrate Firebase Authentication (`src/services/auth.js`)

The existing `authService` in `src/services/auth.js` makes API calls to your backend for authentication. You will modify this service to use Firebase Authentication functions.

1.  **Modify `src/services/auth.js`:**
    Update `src/services/auth.js` to import Firebase Auth and use its methods:

    ```javascript
    // src/services/auth.js
    import { auth, app } from '@/services/firebase'; // Import Firebase auth instance
    import {
      createUserWithEmailAndPassword,
      signInWithEmailAndPassword,
      signOut,
      onAuthStateChanged,
    } from 'firebase/auth';

    // Removed the import for apiService if authentication is fully handled by Firebase
    // import { apiService } from '@/services/api'; 
    import { ValidationUtils } from '@/utils/validation';
    import { CONFIG } from '@/config';

    // Authentication Service for AgriSense
    class AuthService {
      constructor() {
        this.currentUser = null;
        this.unsubscribeAuth = null; // To store the unsubscribe function for auth state changes
      }

      // Initialize auth service and set up Firebase auth state listener
      async init() {
        return new Promise((resolve) => {
          // Listen for Firebase auth state changes
          this.unsubscribeAuth = onAuthStateChanged(auth, async (user) => {
            if (user) {
              // User is signed in.
              // You might want to fetch additional user data (e.g., roles from Firestore) here
              this.currentUser = {
                uid: user.uid,
                email: user.email,
                // Add more user properties as needed, potentially from Firestore
                // For now, let's assume roles are stored in custom claims or Firestore
                role: localStorage.getItem('userRole') || 'farmer' // Default role
              };
              localStorage.setItem('accessToken', user.uid); // Using UID as a token for simplicity
              localStorage.setItem('userRole', this.currentUser.role);
              resolve(true);
            } else {
              // User is signed out.
              this.clearAuth();
              resolve(false);
            }
          });
        });
      }

      // Login method using Firebase Authentication
      async login(email, password) {
        try {
          const userCredential = await signInWithEmailAndPassword(auth, email, password);
          const user = userCredential.user;
          // After successful login, onAuthStateChanged will update this.currentUser
          return { success: true, user: this.currentUser, message: 'Login successful' };
        } catch (error) {
          console.error('Firebase Login error:', error);
          let errorMessage = 'Login failed. Please check your credentials.';
          if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
            errorMessage = 'Invalid email or password.';
          } else if (error.code === 'auth/too-many-requests') {
            errorMessage = 'Access to this account has been temporarily disabled due to many failed login attempts. Please try again later.';
          }
          return { success: false, message: errorMessage };
        }
      }

      // Register method using Firebase Authentication
      async register(userData) {
        try {
          // Validate password strength using ValidationUtils
          const passwordError = ValidationUtils.password(userData.password);
          if (passwordError) {
            return { success: false, message: passwordError };
          }

          const userCredential = await createUserWithEmailAndPassword(auth, userData.email, userData.password);
          const user = userCredential.user;

          // Optionally, store additional user data (like role) in Firestore
          // Example: await setDoc(doc(db, "users", user.uid), { role: userData.role });

          return { success: true, message: 'Registration successful. You can now log in.' };
        } catch (error) {
          console.error('Firebase Registration error:', error);
          let errorMessage = 'Registration failed.';
          if (error.code === 'auth/email-already-in-use') {
            errorMessage = 'The email address is already in use by another account.';
          } else if (error.code === 'auth/invalid-email') {
            errorMessage = 'The email address is not valid.';
          } else if (error.code === 'auth/operation-not-allowed') {
            errorMessage = 'Email/password accounts are not enabled. Enable them in the Firebase console.';
          } else if (error.code === 'auth/weak-password') {
            errorMessage = 'The password is too weak.';
          }
          return { success: false, message: errorMessage };
        }
      }

      // Logout method using Firebase Authentication
      async logout() {
        try {
          await signOut(auth);
          this.clearAuth(); // onAuthStateChanged will also trigger this.clearAuth
          return { success: true, message: 'Logged out successfully' };
        } catch (error) {
          console.error('Firebase Logout error:', error);
          return { success: false, message: error.message || 'Logout failed.' };
        }
      }

      // Clear authentication data
      clearAuth() {
        this.currentUser = null;
        localStorage.removeItem('userRole');
        localStorage.removeItem('accessToken'); // Clear any local token storage
      }

      // Check if user is authenticated
      isAuthenticated() {
        return !!this.currentUser;
      }

      // Get current user role (needs to be implemented based on where roles are stored)
      getUserRole() {
        // This will need to be updated if roles are fetched from Firestore
        return this.currentUser ? this.currentUser.role : null;
      }

      // The following methods (isAdmin, isMiddleman, isFarmer, hasPermission)
      // will depend on how user roles are managed in Firebase.
      // If roles are stored in Firestore, you'll need to fetch them when the user logs in
      // and update this.currentUser.role accordingly.
      isAdmin() {
        return this.getUserRole() === CONFIG.USER_ROLES.ADMIN;
      }

      isMiddleman() {
        return this.getUserRole() === CONFIG.USER_ROLES.MIDDLEMAN;
      }

      isFarmer() {
        return this.getUserRole() === CONFIG.USER_ROLES.FARMER;
      }

      hasPermission(permission) {
        const role = this.getUserRole();
        if (!role) return false;

        const permissions = {
          farmer: [
            'view_own_sensors',
            'control_own_irrigation',
            'view_own_logs',
            'manual_override'
          ],
          middleman: [
            'view_assigned_sensors',
            'view_assigned_logs'
          ],
          admin: [
            'view_all_sensors',
            'view_all_users',
            'control_all_irrigation',
            'retrain_model',
            'manage_users',
            'export_data',
            'view_own_sensors',
            'control_own_irrigation',
            'view_own_logs',
            'manual_override'
          ]
        };

        return permissions[role] && permissions[role].includes(permission);
      }

      // Call this when the component that uses authService is unmounted
      // Or when the app is about to close
      cleanup() {
        if (this.unsubscribeAuth) {
          this.unsubscribeAuth();
        }
      }
    }

    // Create a singleton instance
    export const authService = new AuthService();
    ```

---

## 4. Integrate Firebase Firestore Database (Data Handling)

Since the project already uses `src/services/api.js` for backend communication, you have a choice:
*   **Hybrid Approach:** Continue using `apiService` for some operations (e.g., complex ML models, external API integrations) and use Firestore for real-time sensor data, irrigation logs, and alerts. This allows for a gradual transition.
*   **Full Firebase:** Migrate all data interactions to Firestore.

Given the existing `apiService`, a **Hybrid Approach** might be more suitable initially. We will focus on integrating Firestore for real-time data which Firebase excels at.

1.  **Create a New Service for Firestore Interactions (e.g., `src/services/firestoreService.js`):**
    Create a new file `src/services/firestoreService.js` to manage interactions with Firestore.

    ```javascript
    // src/services/firestoreService.js
    import { db } from '@/services/firebase';
    import {
      collection,
      doc,
      getDoc,
      getDocs,
      setDoc,
      updateDoc,
      deleteDoc,
      query,
      where,
      orderBy,
      limit,
      onSnapshot, // For real-time listeners
    } from 'firebase/firestore';

    class FirestoreService {
      constructor() {
        this.db = db;
      }

      // --- Generic CRUD Operations ---

      async getDocument(collectionName, docId) {
        const docRef = doc(this.db, collectionName, docId);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          return { id: docSnap.id, ...docSnap.data() };
        } else {
          console.log(`No such document: ${collectionName}/${docId}`);
          return null;
        }
      }

      async getCollection(collectionName, queryOptions = {}) {
        let q = collection(this.db, collectionName);

        // Apply where clauses
        if (queryOptions.where) {
          queryOptions.where.forEach(clause => {
            q = query(q, where(clause.field, clause.operator, clause.value));
          });
        }
        // Apply order by
        if (queryOptions.orderBy) {
          queryOptions.orderBy.forEach(order => {
            q = query(q, orderBy(order.field, order.direction));
          });
        }
        // Apply limit
        if (queryOptions.limit) {
          q = query(q, limit(queryOptions.limit));
        }

        const querySnapshot = await getDocs(q);
        const data = [];
        querySnapshot.forEach((doc) => {
          data.push({ id: doc.id, ...doc.data() });
        });
        return data;
      }

      async addDocument(collectionName, data, docId = null) {
        if (docId) {
          await setDoc(doc(this.db, collectionName, docId), data);
          return docId;
        } else {
          const newDocRef = doc(collection(this.db, collectionName));
          await setDoc(newDocRef, data);
          return newDocRef.id;
        }
      }

      async updateDocument(collectionName, docId, data) {
        const docRef = doc(this.db, collectionName, docId);
        await updateDoc(docRef, data);
        return true;
      }

      async deleteDocument(collectionName, docId) {
        const docRef = doc(this.db, collectionName, docId);
        await deleteDoc(docRef);
        return true;
      }

      // --- Real-time Listeners ---
      // This method returns an unsubscribe function to stop listening
      listenToCollection(collectionName, callback, queryOptions = {}) {
        let q = collection(this.db, collectionName);

        if (queryOptions.where) {
          queryOptions.where.forEach(clause => {
            q = query(q, where(clause.field, clause.operator, clause.value));
          });
        }
        if (queryOptions.orderBy) {
          queryOptions.orderBy.forEach(order => {
            q = query(q, orderBy(order.field, order.direction));
          });
        }
        if (queryOptions.limit) {
          q = query(q, limit(queryOptions.limit));
        }

        const unsubscribe = onSnapshot(q, (snapshot) => {
          const data = [];
          snapshot.forEach((doc) => {
            data.push({ id: doc.id, ...doc.data() });
          });
          callback(data);
        }, (error) => {
          console.error("Error listening to collection:", error);
        });

        return unsubscribe;
      }

      listenToDocument(collectionName, docId, callback) {
        const docRef = doc(this.db, collectionName, docId);
        const unsubscribe = onSnapshot(docRef, (docSnap) => {
          if (docSnap.exists()) {
            callback({ id: docSnap.id, ...docSnap.data() });
          } else {
            callback(null);
          }
        }, (error) => {
          console.error("Error listening to document:", error);
        });
        return unsubscribe;
      }
    }

    export const firestoreService = new FirestoreService();
    ```

---

## 5. Update Main Application Entry (`src/main.js`)

You need to initialize your `authService` when your application starts to ensure the Firebase authentication state is checked early.

1.  **Modify `src/main.js`:**
    Update `src/main.js` to call the `authService.init()` method before mounting the Vue app.

    ```javascript
    // src/main.js
    import { createApp } from 'vue';
    import App from './App.vue';
    import router from './router';
    import { authService } from '@/services/auth'; // Import authService

    // Import global CSS
    import '@/css/main.css';
    import 'bootstrap/dist/css/bootstrap.min.css';
    import '@fortawesome/fontawesome-free/css/all.min.css';

    // Import Bootstrap JavaScript (if needed for components like modals, tooltips)
    import 'bootstrap/dist/js/bootstrap.bundle.min.js';

    // Initialize the auth service and wait for it to be ready
    authService.init().then(() => {
      const app = createApp(App);

      app.use(router);

      app.mount('#app');

      // Expose global utility functions if necessary for older components or debugging
      import * as Utils from '@/utils/helpers';
      window.Utils = Utils;

      import * as Config from '@/config';
      window.CONFIG = Config;
    });
    ```

---

## 6. Update Router Navigation Guard (`src/router.js`)

The router already has a navigation guard. You need to ensure it correctly leverages the updated `authService` which is now powered by Firebase. The current logic should still work as `isAuthenticated()` method is updated.

```javascript
// src/router.js (No significant changes needed, but verify logic)
import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '@/views/DashboardView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';
import { authService } from '@/services/auth';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // Wait for authService to initialize its state from Firebase
  // This is important because onAuthStateChanged is asynchronous
  await authService.init(); // This line ensures auth state is ready before checking.

  const requiresAuth = to.meta.requiresAuth;
  const isAuthenticated = authService.isAuthenticated();

  if (requiresAuth && !isAuthenticated) {
    // If the route requires auth and the user is not authenticated, redirect to login
    next('/login');
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    // If the user is authenticated and tries to access login or register, redirect to dashboard
    next('/dashboard');
  } else {
    // Otherwise, allow navigation
    next();
  }
});

export default router;
```
**Note:** The `authService.init()` call inside `router.beforeEach` is generally not ideal as it will run on every route navigation. The primary `authService.init()` in `main.js` should handle the initial state. For subsequent navigations, `authService.isAuthenticated()` should reflect the current state. The key is that `authService.init()` should resolve only once the initial Firebase auth state is established.

A more robust pattern would be to ensure `authService.init()` is called and resolved *once* when the app loads, and then the router guard can rely on its synchronous `isAuthenticated()` method. The `main.js` modification handles this.

---

## 7. Update Components to Use Firebase Services

You will need to update your Vue components to interact with the new Firebase-powered `authService` and `firestoreService`.

### Example: `LoginView.vue`

Modify `LoginView.vue` to use the new Firebase-based login:

```vue
<!-- src/views/LoginView.vue (Example snippet) -->
<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authService } from '@/services/auth'; // Use updated authService

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const router = useRouter();

const handleLogin = async () => {
  errorMessage.value = '';
  const { success, message } = await authService.login(email.value, password.value);
  if (success) {
    router.push('/dashboard');
  } else {
    errorMessage.value = message;
  }
};
</script>

<template>
  <div class="login-container">
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <input type="email" v-model="email" placeholder="Email" required />
      <input type="password" v-model="password" placeholder="Password" required />
      <button type="submit">Login</button>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </form>
    <router-link to="/register">Don't have an account? Register here.</router-link>
  </div>
</template>

<style scoped>
/* Your existing styles */
</style>
```

### Example: `RegisterView.vue`

Modify `RegisterView.vue` to use the new Firebase-based registration:

```vue
<!-- src/views/RegisterView.vue (Example snippet) -->
<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authService } from '@/services/auth'; // Use updated authService

const email = ref('');
const password = ref('');
const role = ref('farmer'); // Default role
const errorMessage = ref('');
const successMessage = ref('');
const router = useRouter();

const handleRegister = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  const userData = { email: email.value, password: password.value, role: role.value };
  const { success, message } = await authService.register(userData);
  if (success) {
    successMessage.value = message + ' Redirecting to login...';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } else {
    errorMessage.value = message;
  }
};
</script>

<template>
  <div class="register-container">
    <h2>Register</h2>
    <form @submit.prevent="handleRegister">
      <input type="email" v-model="email" placeholder="Email" required />
      <input type="password" v-model="password" placeholder="Password" required />
      <select v-model="role">
        <option value="farmer">Farmer</option>
        <option value="middleman">Middleman</option>
        <option value="admin">Admin</option>
      </select>
      <button type="submit">Register</button>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
    </form>
    <router-link to="/login">Already have an account? Login here.</router-link>
  </div>
</template>

<style scoped>
/* Your existing styles */
</style>
```

### Example: Using `firestoreService` for Real-time Data (`SensorDisplay.vue`)

To display real-time sensor data from Firestore, you would modify a component like `SensorDisplay.vue`.

Assume your Firestore structure might look like:
`devices/{deviceId}/sensors/{sensorId}`

```vue
<!-- src/components/SensorDisplay.vue (Example snippet for Firestore) -->
<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { firestoreService } from '@/services/firestoreService'; // Import firestoreService

const props = defineProps({
  deviceId: {
    type: String,
    required: true
  }
});

const sensorData = ref(null);
const unsubscribe = ref(null);

onMounted(() => {
  // Listen to a specific document for real-time updates
  // Example: Listen to a 'latest_readings' document in a 'devices' collection
  unsubscribe.value = firestoreService.listenToDocument(
    `devices/${props.deviceId}/latest_readings`, // Collection path/Doc ID
    'current_data', // Or whatever your document ID is
    (data) => {
      if (data) {
        sensorData.value = data;
      } else {
        console.log('No sensor data found for device:', props.deviceId);
        sensorData.value = null;
      }
    }
  );
});

onUnmounted(() => {
  // Unsubscribe from real-time listener to prevent memory leaks
  if (unsubscribe.value) {
    unsubscribe.value();
  }
});
</script>

<template>
  <div class="sensor-display card">
    <h3>Device: {{ props.deviceId }}</h3>
    <div v-if="sensorData">
      <p>Temperature: {{ sensorData.temperature }}°C</p>
      <p>Humidity: {{ sensorData.humidity }}%</p>
      <p>Soil Moisture: {{ sensorData.moisture }}%</p>
      <p>Last Updated: {{ new Date(sensorData.timestamp?.toDate()).toLocaleString() }}</p>
    </div>
    <div v-else>
      <p>Loading sensor data...</p>
    </div>
  </div>
</template>

<style scoped>
/* Your existing styles */
</style>
```

---

## 8. Consider User Role Management

With Firebase Authentication, user roles (Farmer, Middleman, Admin) are not automatically part of the `user` object. You have several options:

*   **Custom Claims:** Set custom claims on the Firebase Auth user object using a Firebase Function. This allows you to check `user.getIdTokenResult(true).then(idTokenResult => idTokenResult.claims.role)` on the client.
*   **Firestore Document:** Store user roles in a separate Firestore collection (e.g., `users/{uid}/profile` with a `role` field). When a user logs in, fetch their role from Firestore. This is a common and flexible approach.
*   **Backend API:** Continue to rely on your existing backend API to provide user roles after Firebase authentication, potentially exchanging the Firebase ID token for a session token from your backend.

The provided `authService` already has placeholders for role management, assuming roles are stored in `localStorage` or fetched from a user object. You'll need to decide on and implement one of the above strategies to properly populate `this.currentUser.role`.

---

This guide provides a comprehensive overview and detailed code examples for integrating Firebase into your AgriSense frontend. Remember to adapt the Firestore data structures and component logic to match your specific application requirements and database design.
