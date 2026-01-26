import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

// Import global CSS
import '@/css/main.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

// Import Bootstrap JavaScript (if needed for components like modals, tooltips)
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

// Import Firebase initialization
import { firebaseService } from './services/firebase';
import { authService } from './services/auth'; // Import authService

const app = createApp(App);

app.use(router);

// Fetch user data on application startup
import { fetchUser } from '@/store/auth';

// Initialize Firebase first
firebaseService.initialize().then(() => {
  // Set up Firebase Auth state listener after Firebase is initialized
  authService.listenForAuthStateChanges();

  // Then mount the app
  app.mount('#app');
}).catch(error => {
  console.error('Failed to initialize Firebase:', error);
  // Optionally, show an error message to the user or fallback to a different view
  app.mount('#app'); // Still mount the app, maybe with an error state
});


// Expose global utility functions if necessary for older components or debugging
// For a pure Vue app, these should ideally be part of Vue components or global properties
import * as Utils from '@/utils/helpers';
window.Utils = Utils;

import * as Config from '@/config';
window.CONFIG = Config;