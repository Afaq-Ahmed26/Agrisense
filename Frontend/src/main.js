import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

// Import global CSS
import '@/css/main.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@fortawesome/fontawesome-free/css/all.min.css';

// Import Bootstrap JavaScript (if needed for components like modals, tooltips)
import 'bootstrap/dist/js/bootstrap.bundle.min.js';


const app = createApp(App);

app.use(router);

app.mount('#app');

// Expose global utility functions if necessary for older components or debugging
// For a pure Vue app, these should ideally be part of Vue components or global properties
import * as Utils from '@/utils/helpers';
window.Utils = Utils;

import * as Config from '@/config';
window.CONFIG = Config;