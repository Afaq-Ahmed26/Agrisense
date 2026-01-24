import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth'; // Remove onAuthStateChanged
import { getFirestore } from 'firebase/firestore';

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// Using VITE_ prefix for environment variables as common in Vite projects.
// If your project uses VUE_APP_, please adjust the .env file accordingly.
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  // measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID // Uncomment if you have this
};

// Initialize Firebase
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp(); // Initialize only if no app exists

// Initialize Firebase services
const auth = getAuth(app);
const db = getFirestore(app); // Assuming Firestore will be used for user profiles

// Removed authReady promise and onAuthStateChanged from here

export { auth, db }; // Remove authReady from export