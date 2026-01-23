// Configuration file for AgriSense frontend

// Individual exports for components that import them directly
export const MAX_LOGS_DISPLAYED = 10;
export const MAX_ALERTS_DISPLAYED = 5;
export const DEFAULT_DURATION_MINUTES = 15;
export const SENSOR_REFRESH_INTERVAL = 30000;
export const ALERTS_REFRESH_INTERVAL = 60000;
export const CHART_UPDATE_INTERVAL = 60000;

export const SENSOR_THRESHOLDS = {
    MOISTURE_CRITICAL: 20,    // Below this is critical
    MOISTURE_WARNING: 30,     // Between critical and warning is warning
    TEMP_HIGH_WARNING: 40,    // Above this is high temperature warning
    DEVICE_OFFLINE_TIME: 300  // Seconds after which device is considered offline
};

export const CONFIG = {
    // Firebase configuration - replace with your actual Firebase project details
    FIREBASE_CONFIG: {
        apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
        authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
        projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
        storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
        messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
        appId: import.meta.env.VITE_FIREBASE_APP_ID,
        measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
    },

    // API Base URL - adjust to your backend deployment
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000", // Fallback for development

    // Default timeout for API requests (in milliseconds)
    API_TIMEOUT: 10000,

    // Refresh interval for sensor data (in milliseconds)
    SENSOR_REFRESH_INTERVAL: 30000, // 30 seconds

    // Refresh interval for alerts (in milliseconds)
    ALERTS_REFRESH_INTERVAL: 60000, // 1 minute

    // Chart update interval (in milliseconds)
    CHART_UPDATE_INTERVAL: 60000, // 1 minute

    // Default dashboard settings
    DASHBOARD: {
        MAX_LOGS_DISPLAYED: MAX_LOGS_DISPLAYED,
        MAX_ALERTS_DISPLAYED: MAX_ALERTS_DISPLAYED,
        DEFAULT_DURATION_MINUTES: DEFAULT_DURATION_MINUTES
    },

    // Alert types and configurations
    ALERT_TYPES: {
        CRITICAL: {
            priority: 1,
            className: 'alert-danger',
            icon: 'fas fa-exclamation-triangle'
        },
        WARNING: {
            priority: 2,
            className: 'alert-warning',
            icon: 'fas fa-exclamation-circle'
        },
        INFO: {
            priority: 3,
            className: 'alert-info',
            icon: 'fas fa-info-circle'
        }
    },

    // Supported user roles
    USER_ROLES: {
        FARMER: 'farmer',
        MIDDLEMAN: 'middleman',
        ADMIN: 'admin'
    },

    // Default sensor thresholds
    SENSOR_THRESHOLDS: {
        MOISTURE_CRITICAL: 20,    // Below this is critical
        MOISTURE_WARNING: 30,     // Between critical and warning is warning
        TEMP_HIGH_WARNING: 40,    // Above this is high temperature warning
        DEVICE_OFFLINE_TIME: 300  // Seconds after which device is considered offline
    }
};
