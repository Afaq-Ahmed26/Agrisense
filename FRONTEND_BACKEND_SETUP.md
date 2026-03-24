# AgriSense Frontend-Backend Connection Setup Guide

This document outlines the steps to connect the AgriSense frontend and backend systems, including configurations for development without hardware, ML model, or Firebase.

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Virtual environment (recommended)

## Backend Setup

### 1. Environment Setup

```bash
# Navigate to the backend directory
cd /path/to/agrisense/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Backend Configuration

The backend is configured to work without Firebase credentials. When Firebase credentials are not provided, it automatically uses mock services for development.

### 3. Starting the Backend

```bash
cd /path/to/agrisense/backend
source venv/bin/activate  # Activate virtual environment
python start_server.py
```

The backend will be available at `http://localhost:8000`.

## Frontend Setup

### 1. Environment Setup

```bash
# Navigate to the frontend directory
cd /path/to/agrisense/Frontend

# Install dependencies
npm install
```

### 2. Frontend Configuration

The frontend is configured to connect to the backend API. You can customize the API base URL in `src/config.js`:

```javascript
API_BASE_URL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"
```

### 3. Starting the Frontend

```bash
cd /path/to/agrisense/Frontend
npm run dev
```

The frontend will be available at `http://localhost:5173` (or similar available port).

## Connection Flow

1. **Authentication**: The frontend communicates with `/auth/login` and `/auth/register` endpoints
2. **Data Retrieval**: The frontend fetches sensor data, alerts, and irrigation logs from respective backend endpoints
3. **Control Commands**: The frontend sends irrigation commands to the backend
4. **Fallback Mechanism**: If the backend is unavailable, the frontend falls back to mock data services

## Development Features

### Mock Data Services
- When the backend is unavailable, the frontend automatically uses mock data
- Mock data includes devices, sensor readings, irrigation events, and alerts
- Mock authentication generates temporary tokens

### API Service Enhancements
- Automatic fallback to mock services when backend is unreachable
- Proper error handling and user notifications
- Consistent data format between real and mock services

## Testing the Connection

1. Start the backend server
2. Start the frontend server
3. Access the frontend in your browser
4. Register a new user or use existing credentials
5. Verify that data loads and displays correctly
6. Test irrigation controls to ensure they communicate with the backend

## Troubleshooting

### Common Issues

- **Port Already in Use**: The frontend may start on a different port (e.g., 5174 instead of 5173)
- **Backend Unavailable**: The frontend will automatically switch to mock data
- **Firebase Errors**: The backend uses mock Firebase services when credentials are not provided

### Verification Steps

1. Check if backend is running: `curl http://localhost:8000/health`
2. Check if frontend is running: Access the URL shown in the terminal
3. Verify API endpoints: `curl http://localhost:8000/docs`

## Next Steps for Production

1. Configure Firebase credentials in `.env` file
2. Deploy the ML model and configure the backend to use it
3. Connect to real hardware sensors
4. Set up proper authentication and security measures
5. Configure domain and SSL certificates