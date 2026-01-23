// Mock API service for AgriSense frontend
// This service provides mock data when the backend is not available or doesn't have real data yet

import { MOCK_DEVICES, MOCK_SENSOR_READINGS, MOCK_IRRIGATION_EVENTS, MOCK_ALERTS, MOCK_USERS, generateMockSensorReading, generateMockAlert } from '@/services/mock-data';

class MockApiService {
    constructor() {
        this.baseURL = 'http://localhost:8000'; // This is just for reference
        this.token = localStorage.getItem('accessToken') || null;
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('accessToken', token);
        } else {
            localStorage.removeItem('accessToken');
        }
    }

    // Remove authentication token
    removeToken() {
        this.token = null;
        localStorage.removeItem('accessToken');
    }

    // Simulate network delay
    async delay(ms = 500) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Authentication methods
    async login(email, password) {
        await this.delay();
        
        // Simulate login - in a real scenario, this would validate credentials
        if (email && password) {
            // Generate a mock JWT token
            const payload = {
                sub: email,
                role: 'farmer',
                exp: Math.floor(Date.now() / 1000) + (60 * 60) // 1 hour from now
            };
            
            // Simple JWT encoding (not secure, just for demo)
            const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' }));
            const encodedPayload = btoa(JSON.stringify(payload));
            const signature = btoa('signature'); // Not actually signed
            
            const mockToken = `${header}.${encodedPayload}.${signature}`;
            
            return { 
                access_token: mockToken, 
                token_type: 'bearer',
                user: { email, role: 'farmer' }
            };
        }
        
        throw new Error('Invalid credentials');
    }

    async register(userData) {
        await this.delay();
        
        const newUser = {
            id: `user_${Date.now()}`,
            email: userData.email,
            username: userData.username,
            role: userData.role || 'farmer',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            is_active: true
        };
        MOCK_USERS.push(newUser);
        return newUser;
    }

    async logout() {
        await this.delay();
        this.removeToken();
        return { message: 'Logged out successfully' };
    }

    async verifyToken() {
        await this.delay();
        if (this.token && this.currentUser) {
            return { valid: true, user: this.currentUser };
        }
        return { valid: false };
    }

    // Sensor data methods
    async getLatestSensorData(deviceId) {
        await this.delay();
        const readings = MOCK_SENSOR_READINGS.filter(r => r.device_id === deviceId);
        if (readings.length > 0) {
            return readings.reduce((latest, current) => 
                new Date(current.timestamp) > new Date(latest.timestamp) ? current : latest
            );
        }
        return generateMockSensorReading(deviceId);
    }

    async getSensorHistory(deviceId, startDate, endDate) {
        await this.delay();
        let filtered = MOCK_SENSOR_READINGS.filter(r => r.device_id === deviceId);
        
        if (startDate) {
            filtered = filtered.filter(r => new Date(r.timestamp) >= new Date(startDate));
        }
        
        if (endDate) {
            filtered = filtered.filter(r => new Date(r.timestamp) <= new Date(endDate));
        }
        
        return filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    }

    async getSensorHealth(deviceId) {
        await this.delay();
        const device = MOCK_DEVICES.find(d => d.id === deviceId);
        if (!device) {
            throw new Error('Device not found');
        }
        
        const latestReading = await this.getLatestSensorData(deviceId);
        
        return {
            ...device,
            last_reading: latestReading,
            status: 'online',
            last_seen: new Date().toISOString()
        };
    }

    // Irrigation control methods
    async getIrrigationStatus(deviceId) {
        await this.delay();
        return { 
            device_id: deviceId, 
            status: 'active', 
            last_updated: new Date().toISOString(),
            is_running: Math.random() > 0.7
        };
    }

    async startIrrigation(deviceId, durationMinutes = 30) {
        await this.delay();
        return {
            device_id: deviceId,
            status: 'started',
            duration_minutes: durationMinutes,
            start_time: new Date().toISOString(),
            message: `Irrigation started for ${durationMinutes} minutes`
        };
    }

    async stopIrrigation(deviceId) {
        await this.delay();
        // Simulate stopping irrigation
        return {
            device_id: deviceId,
            status: 'stopped',
            stop_time: new Date().toISOString(),
            message: 'Irrigation stopped'
        };
    }

    async getIrrigationLogs(deviceId, limit = 50) {
        await this.delay();
        let filtered = MOCK_IRRIGATION_EVENTS.filter(e => e.device_id === deviceId);
        return filtered.slice(0, limit);
    }

    async getIrrigationPredictions(deviceId, hoursAhead = 48) {
        await this.delay();
        const predictions = [];
        for (let i = 0; i < 5; i++) {
            predictions.push({
                id: `pred_${Date.now()}_${i}`,
                device_id: deviceId,
                predicted_time: new Date(Date.now() + (i + 1) * 24 * 60 * 60 * 1000).toISOString(),
                recommendation: ['irrigate_now', 'consider_irrigation', 'no_irrigation_needed'][i % 3],
                confidence: 0.7 + Math.random() * 0.3,
                reason: ['Low moisture', 'High temperature', 'Optimal conditions'][i % 3]
            });
        }
        return predictions;
    }

    // ML model methods
    async getModelPredictions(data) {
        await this.delay();
        const { soil_moisture, temperature, humidity } = data;
        
        let recommendation = 'no_irrigation_needed';
        let confidence = 0.8;
        
        if (soil_moisture < 30) {
            recommendation = 'irrigate_now';
            confidence = 0.9;
        } else if (soil_moisture < 40) {
            recommendation = 'consider_irrigation';
            confidence = 0.75;
        } else if (temperature > 35 && humidity < 30) {
            recommendation = 'monitor_closely';
            confidence = 0.7;
        }
        
        return {
            recommendation,
            confidence,
            predicted_at: new Date().toISOString(),
            input_data: data
        };
    }

    async retrainModel(datasetStartDate, datasetEndDate) {
        await this.delay(2000);
        return { 
            success: true, 
            message: 'Model retraining completed successfully', 
            estimated_completion: new Date().toISOString()
        };
    }

    async getModelInfo() {
        await this.delay();
        return {
            status: 'operational',
            service: 'ml_service',
            message: 'ML service is ready for predictions',
            model_version: '1.0.0',
            last_trained: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
        };
    }

    // User methods
    async getUserProfile() {
        await this.delay();
        // Return the first mock user as the current user
        return MOCK_USERS[0];
    }

    async updateUserProfile(profileData) {
        await this.delay();
        return { ...profileData, updated_at: new Date().toISOString() };
    }

    async getUsers() {
        await this.delay();
        return MOCK_USERS;
    }

    async deleteUser(userId) {
        await this.delay();
        const index = MOCK_USERS.findIndex(u => u.id === userId);
        if (index !== -1) {
            MOCK_USERS.splice(index, 1);
            return { message: `User ${userId} deleted successfully` };
        }
        throw new Error('User not found');
    }

    // Alert methods
    async getActiveAlerts(deviceId) {
        await this.delay();
        return MOCK_ALERTS.filter(alert => 
            alert.device_id === deviceId && 
            alert.status === 'open'
        );
    }

    async acknowledgeAlert(alertId) {
        await this.delay();
        return { 
            id: alertId, 
            status: 'acknowledged', 
            acknowledged_at: new Date().toISOString() 
        };
    }
}

// Create a singleton instance
export const mockApiService = new MockApiService();