# AgriSense - Web Dashboard

## 🚀 Project Overview

This project is the frontend web dashboard for the AgriSense intelligent irrigation management platform. It allows users to monitor sensor data, control irrigation systems, view predictions, and manage alerts in real-time.

## 🏗️ System Architecture

### Technology Stack
- **Core**: HTML5, CSS3, JavaScript (ES6+)
- **Framework/Libraries**:
  - **Vue.js 3**: For building reactive UI components.
  - **Chart.js**: For data visualization (charts and graphs).
  - **Axios**: For making HTTP requests to the FastAPI backend.
  - **(Optional) Tailwind CSS**: For rapid UI development and responsive design.
  - **(Optional) Socket.IO Client**: For real-time communication if WebSockets are used extensively beyond Firebase Realtime Database listeners.
- **Build Tools**:
  - **Vite**: For an efficient development server, hot module replacement, and optimized production builds.

### File Structure
```
Frontend/
├── public/
│   ├── index.html              # Main HTML file (entry point)
│   ├── register.html           # Registration page
│   ├── favicon.ico
│   └── ... (other static assets like images, icons)
│
├── src/
│   ├── main.js                 # Application entry point, initializes Vue app
│   ├── App.vue                 # Root Vue component
│   ├── router.js               # Vue Router configuration
│   ├── components/
│   │   ├── SensorDisplay.vue     # Displays individual sensor readings
│   │   ├── IrrigationControl.vue # Controls for starting/stopping irrigation
│   │   ├── PredictionChart.vue   # Chart for future water needs
│   │   ├── LogsTable.vue         # Table for irrigation history
│   │   ├── AlertsBanner.vue      # Displays critical/warning alerts
│   │   ├── UserProfile.vue       # User profile display/edit
│   │   ├── AdminPanel.vue        # Admin-specific UI components
│   │   └── ... (other UI components)
│   ├── services/
│   │   ├── api.js              # Axios instance for API calls
│   │   ├── auth.js             # Authentication logic (login, logout, token handling)
│   │   ├── firebase.js         # Firebase initialization and real-time listeners
│   │   └── websocket.js        # WebSocket connection handling (if used)
│   ├── utils/
│   │   ├── helpers.js          # Utility functions (e.g., date formatting)
│   │   └── validation.js       # Client-side form validation
│   ├── css/
│   │   ├── main.css            # Global styles
│   │   ├── components.css      # Component-specific styles (or use SCSS/modules)
│   │   └── ...
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   └── config.js             # Configuration (API base URL, Firebase config)
│
├── vite.config.js          # Vite configuration file
├── package.json            # Project dependencies and scripts
└── README.md               # Project README (this file)
```

---

## 📜 Features by User Role

### 1. Farmer (Full Control)
- **Real-time Display**: Temperature, humidity, soil moisture.
- **Irrigation Control**: Status (ON/OFF), Manual Override (Start/Stop buttons), Mode selection (Auto/Manual).
- **Irrigation Logs**: History table with timestamps, duration, water used.
- **Future Predictions**: Charts showing water needs for the next 24-48 hours.
- **Alerts**: Critical warning banners for low moisture, sensor failures, etc.

### 2. Middleman (View-Only Assistant)
- **View-Only Access**: All sensor data, irrigation status, logs, and predictions.
- **No Control Capabilities**: Cannot start/stop irrigation or change settings.
- **Multi-Device View**: Ability to view data from multiple assigned devices/farmers.

### 3. Admin (System Control)
- **All Farmer Capabilities**.
- **User Management**: View, add, edit, and remove users; assign roles and device access.
- **ML Model Management**: Interface to retrain the ML model, view model version, accuracy, and download datasets.
- **System Health Dashboard**: Overview of all devices, sensors, and user activity.

---

## 🚀 Core Components & Functionality

### 1. Authentication (`src/services/auth.js`, `public/index.html`, `public/register.html`)
- **Login Page**: Handles user login requests using the backend API.
- **Registration Page**: Allows new users to sign up with role selection.
- **Token Management**: Stores JWT tokens (e.g., in localStorage) and handles verification/refresh.
- **Protected Routes**: Ensures only authenticated users can access the dashboard.

### 2. Real-time Data Handling (`src/services/firebase.js`, `src/components/`)
- **Firebase Integration**: Connects to Firebase Realtime Database or Firestore.
- **Listeners**: Sets up listeners to receive real-time updates for sensor data, irrigation status, and alerts.
- **Sensor Display Component**: Updates UI elements dynamically as new data arrives.

### 3. Irrigation Control (`src/components/IrrigationControl.vue`, `src/services/api.js`)
- **Manual Controls**: Buttons for starting/stopping irrigation, with confirmation modals.
- **Mode Selection**: Toggles between Auto and Manual modes.
- **API Integration**: Sends commands to the backend API endpoints (`/irrigation/manual-start`, `/irrigation/manual-stop`).

### 4. Data Visualization (`src/components/PredictionChart.vue`, `src/js/charts.js`)
- **Chart.js Integration**: Renders historical sensor data and future predictions.
- **Dynamic Updates**: Charts update in real-time as new data becomes available.

### 5. Alerts (`src/components/AlertsBanner.vue`)
- **Display Logic**: Shows banners (Red, Yellow, Blue) based on alert severity.
- **Real-time Monitoring**: Listens for new alerts from Firebase or API.

### 6. Admin Features (`src/components/AdminPanel.vue`, `src/services/api.js`)
- **User Management UI**: Forms and tables for managing users.
- **ML Model Interface**: Buttons/forms for retraining, downloading data.

---

## 🛠️ Setup and Installation

1.  **Prerequisites**:
    - Node.js (v18 or higher recommended)
    - npm or yarn (v7 or higher recommended for parallel script execution)
    - Firebase Project Setup (Firestore, Realtime Database, Authentication enabled)

2.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd Frontend
    ```

3.  **Install Dependencies**:
    ```bash
    npm install
    # or
    yarn install
    ```

4.  **Configuration**:
    - Create a `.env` file in the root of the `Frontend` directory.
    - Add your Firebase project configuration details and the backend API base URL.
    ```dotenv
    # Example .env file
    VITE_FIREBASE_API_KEY=YOUR_API_KEY
    VITE_FIREBASE_AUTH_DOMAIN=YOUR_AUTH_DOMAIN
    VITE_FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
    VITE_FIREBASE_STORAGE_BUCKET=YOUR_STORAGE_BUCKET
    VITE_FIREBASE_MESSAGING_SENDER_ID=YOUR_MESSAGING_SENDER_ID
    VITE_FIREBASE_APP_ID=YOUR_APP_ID
    VITE_FIREBASE_MEASUREMENT_ID=YOUR_MEASUREMENT_ID

    VITE_API_BASE_URL=http://localhost:8000/api/v1
    ```
    *Note: Ensure all Firebase and API related variables are prefixed with `VITE_` for Vite compatibility.*

5.  **Run Development Server**:
    ```bash
    npm run dev
    # or
    yarn dev
    ```
    This command starts the development server, typically accessible at `http://localhost:5173` (Vite's default). It includes hot module replacement for a smooth development experience.

6.  **Build for Production**:
    ```bash
    npm run build
    # or
    yarn build
    ```
    This command generates an optimized production build in the `dist/` directory. The contents of this directory are ready for deployment.

---

## ☁️ Deployment Recommendations

- **Static Hosting**: Deploy the contents of the `dist/` folder to services like:
  - **Firebase Hosting**: Highly recommended due to seamless integration with Firebase services (Authentication, Firestore, Realtime Database).
  - **Netlify / Vercel**: Offer excellent CI/CD pipelines, global CDN, and easy configuration.
  - **AWS S3 + CloudFront**: A scalable and robust solution for hosting static assets.

- **CI/CD**: Implement a Continuous Integration/Continuous Deployment pipeline (e.g., using GitHub Actions, GitLab CI) to automate the build and deployment process upon code commits.

---

## 📄 Documentation

- **API Documentation**: Automatically generated by FastAPI and accessible via the backend's `/docs` endpoint (Swagger UI).
- **Code Comments**: Comprehensive inline comments are provided within the codebase to explain logic, component props, and service functions.
- **README.md**: This file serves as the primary documentation, offering a high-level overview, setup instructions, and architectural details.
