// Standalone mock API server for AgriSense frontend
// Run this with Node.js to serve mock backend endpoints

import express from 'express';
import cors from 'cors';
import path from 'path';

const app = express();
const port = 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Mock data store
let mockSensorData = {
    moisture: 45.8,
    temperature: 25.5,
    humidity: 65.2,
    timestamp: Date.now()
};

let mockIrrigationStatus = {
    valve_open: false,
    mode: 'auto',
    last_irrigation: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    duration_minutes: 20
};

let mockAlerts = [
    {
        id: 'alert1',
        type: 'moisture_warning',
        message: 'WARNING: Soil moisture level approaching threshold',
        severity: 'warning',
        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        acknowledged: false
    }
];

let mockLogs = [
    {
        id: 1,
        start_time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        duration_minutes: 30,
        water_used_liters: 120,
        mode: 'auto',
        status: 'Completed'
    },
    {
        id: 2,
        start_time: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
        duration_minutes: 25,
        water_used_liters: 100,
        mode: 'manual',
        status: 'Completed'
    }
];

let mockPredictions = [];
for (let i = 0; i < 48; i++) { // 48 hours ahead
    const time = new Date(Date.now() + i * 60 * 60 * 1000);
    mockPredictions.push({
        time: time.toISOString(),
        irrigation_needed: Math.random() > 0.7,
        water_liters: Math.floor(Math.random() * 100) + 50,
        confidence: Math.random() * 0.3 + 0.7
    });
}

// Mock authentication endpoint
app.post('/api/v1/auth/login', (req, res) => {
    const { email, password } = req.body;
    
    // Accept any non-empty credentials for demo purposes
    if (email && password) {
        return res.json({
            access_token: 'demo_jwt_token_' + Date.now(),
            user: {
                email: email,
                name: email.split('@')[0],
                role: 'farmer'
            },
            role: 'farmer'
        });
    }
    
    res.status(401).json({ message: 'Invalid credentials' });
});

app.post('/api/v1/auth/register', (req, res) => {
    res.json({ success: true, message: 'Registration successful. Please login.' });
});

app.get('/api/v1/auth/verify', (req, res) => {
    res.json({
        valid: true,
        user: {
            email: 'demo@example.com',
            name: 'Demo User',
            role: 'farmer'
        }
    });
});

// Mock sensor data endpoint
app.get('/api/v1/sensors/latest', (req, res) => {
    // Simulate slight variations in sensor data
    mockSensorData = {
        moisture: 40 + Math.random() * 20,
        temperature: 20 + Math.random() * 15,
        humidity: 50 + Math.random() * 30,
        timestamp: Date.now()
    };
    
    res.json(mockSensorData);
});

// Mock irrigation status endpoint
app.get('/api/v1/irrigation/status', (req, res) => {
    res.json(mockIrrigationStatus);
});

// Mock start irrigation endpoint
app.post('/api/v1/irrigation/manual-start', (req, res) => {
    const { duration_minutes } = req.body;
    mockIrrigationStatus.valve_open = true;
    mockIrrigationStatus.mode = 'manual';
    
    // Add to logs
    mockLogs.unshift({
        id: mockLogs.length + 1,
        start_time: new Date().toISOString(),
        duration_minutes: duration_minutes,
        water_used_liters: Math.floor(duration_minutes * 4),
        mode: 'manual',
        status: 'Running'
    });
    
    res.json({ message: 'Irrigation started successfully' });
});

// Mock stop irrigation endpoint
app.post('/api/v1/irrigation/manual-stop', (req, res) => {
    mockIrrigationStatus.valve_open = false;
    
    // Update latest log to completed
    if (mockLogs.length > 0) {
        mockLogs[0].status = 'Completed';
    }
    
    res.json({ message: 'Irrigation stopped successfully' });
});

// Mock irrigation logs endpoint
app.get('/api/v1/irrigation/logs', (req, res) => {
    res.json({ logs: mockLogs.slice(0, 10) });
});

// Mock irrigation predictions endpoint
app.get('/api/v1/irrigation/predictions', (req, res) => {
    res.json({ predictions: mockPredictions });
});

// Mock alerts endpoint
app.get('/api/v1/alerts/active', (req, res) => {
    res.json({ alerts: mockAlerts.filter(alert => !alert.acknowledged) });
});

// Mock acknowledge alert endpoint
app.put('/api/v1/alerts/:alertId/acknowledge', (req, res) => {
    const alertId = req.params.alertId;
    const alert = mockAlerts.find(a => a.id === alertId);
    if (alert) {
        alert.acknowledged = true;
    }
    res.json({ message: 'Alert acknowledged' });
});

// Catch-all route to serve frontend if deployed together
app.get(/^\/(?!api\/v1).*$/, (req, res) => {
    res.json({ message: 'This is a mock API server for AgriSense frontend. The actual API endpoints are available at /api/v1/...' });
});

// Start server
app.listen(port, () => {
    console.log(`Mock API server running at http://localhost:${port}`);
    console.log('Available endpoints:');
    console.log('  POST /api/v1/auth/login - Login');
    console.log('  GET /api/v1/sensors/latest - Latest sensor data');
    console.log('  GET /api/v1/irrigation/status - Irrigation status');
    console.log('  POST /api/v1/irrigation/manual-start - Start irrigation');
    console.log('  POST /api/v1/irrigation/manual-stop - Stop irrigation');
    console.log('  And more...');
    console.log('\nTo use with the frontend, make sure your .env file sets VITE_API_BASE_URL=http://localhost:8000/api/v1');
});

// Update sensor data periodically to simulate changes
setInterval(() => {
    mockSensorData = {
        moisture: 40 + Math.random() * 20,
        temperature: 20 + Math.random() * 15,
        humidity: 50 + Math.random() * 30,
        timestamp: Date.now()
    };
}, 30000); // Update every 30 seconds