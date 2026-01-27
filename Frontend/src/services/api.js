import { CONFIG } from '@/config';

// API Service for AgriSense - handles all backend communication
class ApiService {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.timeout = CONFIG.API_TIMEOUT;
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

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(this.token && { 'Authorization': `Bearer ${this.token}` })
            },
            timeout: this.timeout
        };

        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...requestOptions,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('Request timeout, falling back to mock data:', endpoint);
            } else {
                console.warn('API request failed, falling back to mock data:', error.message, endpoint);
            }

            // Import mock API service and use it as fallback
            const { mockApiService } = await import('@/services/mock-api.js');

            // Map endpoints to mock API methods
            if (endpoint.includes('/auth/login')) {
                // For login, we need to extract email and password from URL
                const urlParams = new URLSearchParams(endpoint.split('?')[1]);
                return mockApiService.login(urlParams.get('email'), urlParams.get('password'));
            } else if (endpoint.includes('/sensors/') && endpoint.includes('/readings')) {
                const deviceId = endpoint.split('/')[2]; // Extract device ID from URL
                return mockApiService.getSensorHistory(deviceId);
            } else if (endpoint.includes('/sensors/')) {
                const deviceId = endpoint.split('/')[2].split('?')[0]; // Extract device ID from URL
                return mockApiService.getSensorHealth(deviceId);
            } else if (endpoint.includes('/alerts/')) {
                if (endpoint.includes('/acknowledge')) {
                    const alertId = endpoint.split('/')[2].split('/')[0]; // Extract alert ID
                    return mockApiService.acknowledgeAlert(alertId);
                } else {
                    // For GET /alerts/, we need to extract device_id from query params
                    const urlParams = new URLSearchParams(endpoint.split('?')[1]);
                    const deviceId = urlParams.get('device_id');
                    return mockApiService.getActiveAlerts(deviceId);
                }
            } else if (endpoint.includes('/irrigation/simulate')) {
                // Extract device_id and duration_minutes from query params
                const urlParams = new URLSearchParams(endpoint.split('?')[1]);
                const deviceId = urlParams.get('device_id');
                const duration = parseInt(urlParams.get('duration_minutes') || '30');
                return mockApiService.startIrrigation(deviceId, duration);
            } else if (endpoint.includes('/irrigation/recommendations/')) {
                const deviceId = endpoint.split('/')[3];
                return mockApiService.getIrrigationPredictions(deviceId);
            } else if (endpoint.includes('/irrigation/events')) {
                return mockApiService.getIrrigationLogs('all');
            } else if (endpoint.includes('/users/me')) {
                return mockApiService.getUserProfile();
            } else if (endpoint.includes('/users/') && options.method === 'PATCH') {
                const userId = endpoint.split('/')[2];
                const userData = JSON.parse(options.body);
                return mockApiService.updateUser(userId, userData);
            } else if (endpoint.includes('/users/')) {
                return mockApiService.getUsers();
            } else if (endpoint.includes('/ml/predict')) {
                // For ML predict, we need to handle the POST differently
                // This will be handled by the calling function
                throw error; // Let the calling function handle this
            } else if (endpoint.includes('/ml/status')) {
                return mockApiService.getModelInfo();
            }

            // If we reach here, throw the original error
            throw error;
        }
    }

    // Authentication methods
    async login(email, password) {
        // The backend expects email and password as query parameters
        const params = new URLSearchParams({
            email: email,
            password: password
        });

        return this.request(`/auth/login?${params}`, {
            method: 'POST'
        });
    }

    async register(userData) {
        console.log('DEBUG: apiService.register - Sending userData:', userData);
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }

    async verifyToken() {
        return this.request('/auth/verify', {
            method: 'GET'
        });
    }

    // Sensor data methods
    async getLatestSensorData(deviceId) {
        // Get all sensors and find the one with the specified device ID
        const sensors = await this.request('/sensors/');
        return sensors.find(sensor => sensor.id === deviceId) || null;
    }

    async getSensorHistory(deviceId, startDate, endDate) {
        const params = new URLSearchParams({
            start_time: startDate,
            end_time: endDate
        });
        return this.request(`/sensors/${deviceId}/readings?${params}`);
    }

    async getSensorHealth(deviceId) {
        return this.request(`/sensors/${deviceId}`, {
            method: 'GET'
        });
    }

    // Irrigation control methods
    async getIrrigationStatus(deviceId) {
        // For now, return a mock status since the backend doesn't have a specific status endpoint
        return { device_id: deviceId, status: 'active', last_updated: new Date().toISOString() };
    }

    async startIrrigation(deviceId, durationMinutes) {
        // Use the simulate endpoint since we don't have hardware
        const params = new URLSearchParams({
            device_id: deviceId,
            duration_minutes: durationMinutes.toString()
        });
        return this.request(`/irrigation/simulate?${params}`, {
            method: 'POST'
        });
    }

    async stopIrrigation(deviceId) {
        // For now, return a mock response since we don't have a stop endpoint
        return { device_id: deviceId, status: 'stopped', stopped_at: new Date().toISOString() };
    }

    async getIrrigationLogs(deviceId, limit = 50) {
        // Get irrigation events for the device
        const events = await this.request('/irrigation/events');
        // Filter for the specific device and limit results
        return events.filter(event => event.device_id === deviceId).slice(0, limit);
    }

    async getIrrigationPredictions(deviceId, hoursAhead = 48) {
        // Get recommendations for the device
        return this.request(`/irrigation/recommendations/${deviceId}`);
    }

    // ML model methods
    async getModelPredictions(data) {
        try {
            return await this.request('/ml/predict', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        } catch (error) {
            console.warn('ML predict failed, falling back to mock data:', error.message);
            const { mockApiService } = await import('@/services/mock-api.js');
            return mockApiService.getModelPredictions(data);
        }
    }

    async retrainModel(datasetStartDate, datasetEndDate) {
        // The backend doesn't have a retrain endpoint, so we'll return a mock response
        return {
            success: true,
            message: 'Model retraining initiated (mock)',
            estimated_completion: new Date(Date.now() + 300000).toISOString() // 5 minutes from now
        };
    }

    async getModelInfo() {
        return this.request('/ml/status');
    }

    // User methods
    async getMe() {
        // Use the /users/me endpoint to get current user profile
        return this.request('/users/me');
    }

    async updateUser(userId, userData) {
        return this.request(`/users/${userId}`, {
            method: 'PATCH',
            body: JSON.stringify(userData)
        });
    }

    async getUsers() {
        return this.request('/users/');
    }

    async deleteUser(userId) {
        return this.request(`/users/${userId}`, {
            method: 'DELETE'
        });
    }

    // Alert methods
    async getActiveAlerts(deviceId) {
        // Get all alerts and filter for the specific device and active status
        const allAlerts = await this.request('/alerts/');
        return allAlerts.filter(alert =>
            alert.device_id === deviceId &&
            alert.status === 'open'
        );
    }

    async acknowledgeAlert(alertId) {
        return this.request(`/alerts/${alertId}/acknowledge`, {
            method: 'POST'  // Changed to POST as the backend uses POST for acknowledge
        });
    }
}

// Create a singleton instance
export const apiService = new ApiService();