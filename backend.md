# AgriSense Backend Development Plan (Simulated Hardware)

## 1. Project Overview & Goal

The AgriSense backend will serve as the central intelligence for our smart irrigation system. Its primary goal is to manage sensor data, control irrigation, provide alerts, and eventually integrate machine learning for optimized water usage. This plan details the backend development stages, emphasizing the use of simulated data to ensure progress continues unhindered by the current lack of ESP32 hardware.

**Backend Goal:**
- Ingest and process sensor data (real or simulated).
- Store historical and real-time data efficiently.
- Enable manual and automated irrigation control.
- Generate critical alerts for system health and irrigation needs.
- Support multi-user roles (Farmer, Middleman, Admin) with appropriate access controls.
- Provide a robust API for frontend interaction and future ML integration.
- Be designed for seamless integration with ESP32 hardware when available, minimizing redesign effort.

## 2. Technology Stack

-   **Framework**: FastAPI (Python)
-   **Database**: Firebase (Firestore for structured data, Realtime Database for real-time updates/state)
-   **Authentication**: Firebase Authentication with JWT for session management.
-   **ML Integration**: Python, scikit-learn (for future model training and inference API).
-   **Data Simulation**: Python scripts and/or FastAPI endpoints to generate mock sensor data.
-   **Communication**: HTTPS for API requests, WebSockets for real-time dashboard updates.

## 3. Core Design Principle: Hardware Independence

**Crucially, the backend must operate independently of the physical hardware.** All functionalities requiring hardware interaction (sensor readings, irrigation commands) will be abstracted and initially simulated.

-   **Simulation Strategy**: Implement mock API endpoints or background services that generate realistic sensor data and respond to irrigation commands as if they were received from an ESP32.
-   **Abstraction Layer**: Design data models and API interfaces to be hardware-agnostic. For example, instead of directly interacting with a sensor ID, we'll interact with a `device_id` which internally maps to a simulated or real sensor.
-   **Future Integration**: When ESP32 hardware is available, the simulation layer will be phased out or replaced by direct hardware communication logic, with minimal changes to the core API and data models.

---

## Development Phases

### Phase 1: Foundation & Project Setup

**Objective**: Establish a robust project structure, configure the FastAPI application, and set up essential services like Firebase integration and basic API endpoints. Ensure the backend can run locally and connect to Firebase.

**Tasks**:
1.  Initialize FastAPI project structure (`backend/app/` as per `CLAUDE.md`).
2.  Configure environment variables (`.env` file management, using `.env.example`).
3.  Integrate Firebase Admin SDK for backend access to Firestore and Realtime Database.
4.  Implement basic API health check endpoint (e.g., `/health`).
5.  Set up basic logging.

**Deliverables**:
-   Runnable FastAPI server in development mode.
-   Successful Firebase project initialization and connection test.

### Phase 2: Authentication & User Management

**Objective**: Implement secure user authentication and role-based access control (RBAC) to manage user permissions.

**User Roles**:
-   `Farmer`: Manages their own devices and data.
-   `Middleman`: Oversees multiple farmers' data (requires specific permissions).
-   `Admin`: System-wide management, user, and device administration.

**Tasks**:
1.  Implement user registration API (using Firebase Auth).
2.  Implement user login API, generating JWT tokens upon successful authentication.
3.  Create middleware for JWT validation and user session management.
4.  Implement RBAC logic to restrict access to endpoints based on user roles.
5.  Define user data models (e.g., `User` model in `backend/app/models/user.py`).

**Deliverables**:
-   Secure API endpoints protected by authentication and authorization.
-   Functional user registration, login, and role management.

### Phase 3: Device & Sensor Data Models (Hardware Agnostic)

**Objective**: Define the data structures for devices and sensor readings, designing them to accommodate both simulated and future real hardware data.

**Device Concept**:
-   Each physical or simulated device will have a unique `device_id`.
-   Devices will be linked to an `owner` (farmer's user ID).
-   Each device will have associated sensor readings and irrigation status.

**Tasks**:
1.  Design Firestore schemas for devices, including metadata (location, owner, type) and potentially historical sensor data summaries.
2.  Define Pydantic models for sensor readings (e.g., `soil_moisture`, `temperature`, `humidity`, `timestamp`).
3.  Define Pydantic models for device status and irrigation control commands.
4.  Implement API endpoints for device registration/management (CRUD operations).

**Deliverables**:
-   Well-defined data models for devices and sensor readings.
-   Firestore collections structured for efficient querying.
-   APIs to manage devices.

### Phase 4: Sensor Data Simulation

**Objective**: Create a mechanism to generate and ingest simulated sensor data into the backend, crucial for testing all other components without hardware.

**Simulation Strategy**:
-   A dedicated Python script or a FastAPI endpoint (e.g., `/mock/sensors/push`) will generate realistic, time-series sensor data.
-   This simulated data will be pushed to the appropriate Firebase Realtime Database or Firestore collections.

**Tasks**:
1.  Develop a data simulation script/service.
2.  Implement logic to generate varied and plausible sensor values (e.g., fluctuations, anomalies).
3.  Integrate with Firebase to store simulated sensor readings.
4.  Ensure the simulation mimics the expected data format and frequency from ESP32 devices.

**Deliverables**:
-   A continuous stream of simulated sensor data populating the database.
-   Backend components (alerts, dashboards) can process this data as if it were real.

### Phase 5: Irrigation Control Logic (Manual First)

**Objective**: Implement the core logic for controlling irrigation, starting with manual user commands.

**Manual Irrigation Flow**:
1.  User (Farmer) sends a command (e.g., "start irrigation", "stop irrigation") via the API.
2.  Backend authenticates and authorizes the user.
3.  Backend records the command and updates the device's irrigation status in Firebase.
4.  The simulation layer (or eventually, the ESP32) acknowledges and executes the command.

**Tasks**:
1.  Implement API endpoints for manual irrigation control (start, stop, set duration).
2.  Log all irrigation events (start time, end time, duration, user, device).
3.  Update device status in Realtime Database to reflect current irrigation state (e.g., `irrigating: true`, `last_irrigation_end: timestamp`).

**Deliverables**:
-   Functional manual irrigation control via the backend API.
-   Accurate logging of irrigation activities.

### Phase 6: Alerting System (Rule-Based)

**Objective**: Develop a system to monitor sensor data and system status, generating alerts for critical conditions.

**Alert Examples**:
-   Low soil moisture thresholds.
-   Sensor data staleness or missing updates.
-   Device offline/unreachable.
-   Irrigation system failures.

**Tasks**:
1.  Define a clear set of rules and thresholds for generating alerts (these may be configurable later).
2.  Implement a background process or trigger mechanism that evaluates incoming sensor data against alert rules.
3.  Store generated alerts in Firestore, including details like type, severity, device, timestamp, and status (e.g., `open`, `acknowledged`).
4.  Implement an API endpoint for fetching alerts and for users to acknowledge them.

**Deliverables**:
-   Automated alert generation based on predefined rules.
-   A mechanism for users to view and manage alerts.

### Phase 7: ML Integration Readiness

**Objective**: Prepare the backend infrastructure to integrate a machine learning model for predictive irrigation, without implementing the full ML pipeline yet.

**Key Principle**: The backend should be ready to *consume* ML predictions, not necessarily train models initially.

**Tasks**:
1.  Structure the `backend/app/services/ml_service.py` and related files.
2.  Create a placeholder prediction API endpoint (e.g., `/ml/predict`) that can return dummy predictions or results based on simple rules.
3.  Define the expected input data format for the ML model (features derived from sensor data, device info, etc.).
4.  Define the output format for ML predictions (e.g., recommended irrigation duration, optimal time).
5.  Ensure data aggregation and feature engineering logic can be developed separately.

**Deliverables**:
-   A skeleton ML service and prediction API endpoint.
-   Backend prepared to ingest and act upon ML-driven recommendations.

### Phase 8: Testing, Validation & Deployment Preparation

**Objective**: Ensure the backend is stable, reliable, and ready for deployment, even with simulated hardware.

**Testing Strategy**:
-   **Unit Tests**: For individual components and utility functions.
-   **Integration Tests**: Testing interactions between services (e.g., API -> Firebase -> Simulation).
-   **End-to-End Tests**: Simulating user flows (registration, device control, alert generation) using the simulated data.
-   **API Testing**: Use tools like Postman or `httpx` to test all API endpoints thoroughly.
-   **RBAC Testing**: Verify all role-based access controls function correctly.

**Tasks**:
1.  Write comprehensive unit and integration tests for all implemented modules.
2.  Develop end-to-end test scenarios covering core functionalities.
3.  Perform load testing on simulation endpoints to ensure scalability.
4.  Prepare deployment configurations (e.g., Dockerfile, initial environment setup).

**Deliverables**:
-   A robust suite of tests covering critical backend functionalities.
-   A stable, well-tested backend ready for deployment.

---

## Final Backend State (Pre-Hardware)

Upon completion of these phases, the AgriSense backend will be a fully functional, secure, and scalable system capable of managing simulated agricultural data and irrigation controls. It will be poised for seamless integration with the ESP32 hardware, allowing for a smooth transition from simulation to real-world operation. The backend will support user roles, generate alerts, and have a prepared pipeline for future ML model integration.
