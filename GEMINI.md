# AgriSense Project Instructions

Welcome to the AgriSense project! This document outlines the architecture, conventions, and workflows for our smart irrigation system.

## Project Overview

AgriSense is an IoT-enabled smart irrigation system that integrates real-time sensor data, machine learning for predictive irrigation, and a web-based dashboard for farmers and administrators.

### Core Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Vue.js 3 (Vite, Pinia-like store structure)
- **Database**: Firebase (Firestore & Realtime Database)
- **IoT**: ESP32 (C++/Arduino)
- **ML**: Scikit-learn (Python)

---

## Architecture & Conventions

### 1. Backend (FastAPI)
- **Location**: `/backend`
- **Structure**:
  - `app/routes`: API endpoints grouped by resource.
  - `app/services`: Business logic and external service integrations (Firebase, ML).
  - `app/repositories`: Database abstraction layer.
  - `app/models`: Pydantic schemas for request/response validation.
- **Standards**:
  - Use Pydantic models for all API inputs and outputs.
  - Implement Role-Based Access Control (RBAC) using dependency injection in routes.
  - Follow the `Repository -> Service -> Route` flow.

### 2. Frontend (Vue.js)
- **Location**: `/Frontend`
- **Structure**:
  - `src/components`: Reusable UI elements.
  - `src/views`: Page-level components.
  - `src/services`: API client (`api.js`) and Firebase integration.
  - `src/store`: State management modules.
- **Standards**:
  - Use the Composition API for new components.
  - All API calls MUST go through `apiService` in `src/services/api.js`.
  - Maintain styling consistency using `src/css/main.css`.

### 3. IoT (ESP32)
- **Location**: `/AgriSense_ESP32.ino`
- **Conventions**:
  - Maintain hardware abstraction: ensure the code can run even if some sensors are disconnected.
  - Use JSON for all communication with the backend.

### 4. Machine Learning
- **Location**: `/model`
- **Workflow**:
  - Training scripts should produce a serialized model (`.pkl`).
  - The backend `ml_service.py` is responsible for loading the model and providing inference.

---

## Development Workflows

### 1. Environment Setup
- **Backend**: Create a virtual environment and install dependencies from `backend/requirements.txt`.
- **Frontend**: Install dependencies using `npm install`.
- **Firebase**: Ensure `firebase-credentials.json` is present in the `backend/` directory (not tracked in Git).

### 2. Database Modifications
- When modifying Firestore schemas, update the corresponding Pydantic models in `backend/app/models/` and reflect changes in `Frontend/src/services/api.js` if necessary.

### 3. Testing
- **Backend**: Use `pytest`. Run tests from the `backend/` directory.
- **Frontend**: Use Vitest (if configured) or manual verification via the dev server.
- **IoT**: Use Serial Monitor for debugging ESP32 behavior.

---

## Security & Safety
- **DO NOT** commit `.env` files or `firebase-credentials.json`.
- Always use the `.env.example` as a template for local environment configuration.
- Follow the principle of least privilege when assigning Firebase roles or API access.
