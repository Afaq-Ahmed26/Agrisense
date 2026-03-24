import { CONFIG } from '@/config';
import { firebaseService } from './firebase'; // Import firebaseService
import { logout as storeLogout, setUser } from '@/store/auth'; // Import setUser and storeLogout

// API Service for AgriSense - handles all backend communication
class ApiService {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.timeout = CONFIG.API_TIMEOUT;
        // this.token no longer explicitly stored here; always fetched from localStorage
        this.isRefreshing = false; // Flag to prevent multiple refresh attempts
        this.failedQueue = []; // Queue for requests that failed due to expired token
    }





    // Helper to process the queue of failed requests
    processQueue(error = null, token = null) {
        this.failedQueue.forEach(prom => {
            if (error) {
                prom.reject(error);
            } else {
                prom.resolve(token);
            }
        });
        this.failedQueue = [];
    }

    // Generic API request method with token refresh logic
    async request(endpoint, options = {}, isRetry = false) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                // Always get the latest token from localStorage
                ...(localStorage.getItem('accessToken') && { 'Authorization': `Bearer ${localStorage.getItem('accessToken')}` })
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

            // Handle token expiration / unauthorized access
            if ((response.status === 401 || response.status === 403) && firebaseService.auth.currentUser && !isRetry) {
                console.warn(`Token expired or unauthorized for ${endpoint}, attempting to refresh...`);
                // This creates a promise that will resolve/reject once token refresh is done
                return new Promise((resolve, reject) => {
                    this.failedQueue.push({ resolve, reject });
                    
                    if (!this.isRefreshing) {
                        this.isRefreshing = true;
                        if (!firebaseService.auth.currentUser) {
                            console.error("Firebase currentUser is null during token refresh attempt. Logging out.");
                            storeLogout();
                            this.processQueue(new Error("No user to refresh token."), null);
                            this.isRefreshing = false; // Reset flag
                            return reject(new Error("No user to refresh token.")); // Reject the outer promise and exit
                        }
                        firebaseService.auth.currentUser.getIdToken(true)
                            .then(refreshedToken => {
                                // Update authStore token and localStorage
                                if (firebaseService.auth.currentUser) {
                                    setUser(firebaseService.auth.currentUser, refreshedToken);
                                }
                                this.processQueue(null, refreshedToken); // Process all queued requests
                                resolve(refreshedToken); // Resolve the outer promise
                            })
                            .catch(err => {
                                console.error('Failed to refresh Firebase ID token:', err);
                                this.processQueue(err); // Process all queued requests with error
                                storeLogout(); // Logout if refresh itself fails
                                reject(err); // Reject the outer promise
                            })
                            .finally(() => {
                                this.isRefreshing = false; // Reset refresh flag
                            });
                    }
                    // If this.isRefreshing is true, the current request is already in the failedQueue,
                    // and its resolution/rejection will be handled by processQueue when the ongoing refresh finishes.
                }).then((refreshedToken) => {
                    // Retry the original request with the new token
                    const newOptions = { ...options };
                    newOptions.headers = {
                        ...newOptions.headers,
                        'Authorization': `Bearer ${refreshedToken}`
                    };
                    return this.request(endpoint, newOptions, true); // Mark as retry
                }).catch(err => {
                    // If token refresh or retry fails, re-throw the error
                    storeLogout();
                    throw new Error(`Failed to refresh token or retry request: ${err.message}`);
                });
            } else if ((response.status === 401 || response.status === 403) && isRetry) {
                // If it's a retry and still 401/403, something is wrong, force logout
                storeLogout();
                throw new Error(`Authentication failed on retry. Please login again. Status: ${response.status}`);
            }

            if (!response.ok) {
                // For other non-OK responses, try to parse JSON error message if available
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const errorJson = await response.json();
                    if (errorJson && errorJson.detail) {
                        errorMessage = `HTTP error! status: ${response.status}. Detail: ${errorJson.detail}`;
                    }
                } catch (jsonError) {
                    // Ignore JSON parsing errors, use generic message
                }
                throw new Error(errorMessage);
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
            } else if (endpoint.includes('/irrigation/trigger')) { // Updated to trigger
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
    async getSensorById(deviceId) {
        return this.request(`/sensors/${deviceId}`, { method: 'GET' });
    }

    async getLatestSensorReadings(deviceId) {
        return this.request(`/sensors/${deviceId}/latest-reading`);
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

    async getDevices() { // New method to get all devices
        return this.request('/sensors/');
    }

    // Irrigation control methods
    async getIrrigationStatus(deviceId) {
        // For now, return a mock status since the backend doesn't have a specific status endpoint
        return { device_id: deviceId, status: 'active', last_updated: new Date().toISOString() };
    }

    async startIrrigation(deviceId, durationSeconds) {
        // Use the simulate endpoint since we don't have hardware
        const params = new URLSearchParams({
            device_id: deviceId,
            duration_seconds: durationSeconds.toString() // Change to duration_seconds
        });
        return this.request(`/irrigation/trigger?${params}`, {
            method: 'POST'
        });
    }

    async triggerIrrigation(deviceId, predictedDurationSeconds) {
        // Pass predictedDurationSeconds directly
        return this.startIrrigation(deviceId, predictedDurationSeconds);
    }

    async stopIrrigation(deviceId) {
        // Call the backend endpoint to stop irrigation
        return this.request(`/irrigation/stop/${deviceId}/`, {
            method: 'POST'
        });
    }

    async getIrrigationLogs(deviceId, limit = 50) {
        // Get irrigation events for the device
        const events = await this.request('/irrigation/events/');
        // Filter for the specific device and limit results
        return events.filter(event => event.device_id === deviceId).slice(0, limit);
    }

    async getIrrigationPredictions(deviceId, hoursAhead = 48) {
        // Get recommendations for the device
        const params = new URLSearchParams({ hours_ahead: hoursAhead });
        return this.request(`/ml/future_predictions/${deviceId}?${params}`);
    }

    // ML model methods
    async getMLPrediction(soil_moisture, temperature, humidity, light_level, device_id = null) {
        try {
            const data = { soil_moisture, temperature, humidity, light_level };
            if (device_id) {
                data.device_id = device_id;
            }
            return await this.request('/ml/predict', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        } catch (error) {
            console.warn('ML predict failed, falling back to mock data:', error.message);
            const { mockApiService } = await import('@/services/mock-api.js');
            return mockApiService.getModelPredictions({ soil_moisture, temperature, humidity, light_level, device_id });
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

    async getUserPreferences(userId) {
        return this.request(`/users/${userId}/preferences`);
    }

    async updateUserPreferences(userId, preferences) {
        return this.request(`/users/${userId}/preferences`, {
            method: 'PUT',
            body: JSON.stringify(preferences)
        });
    }

    async getUserNotificationPreferences(userId) {
        return this.request(`/users/${userId}/notification-preferences`);
    }

    async updateUserNotificationPreferences(userId, preferences) {
        return this.request(`/users/${userId}/notification-preferences`, {
            method: 'PUT',
            body: JSON.stringify(preferences)
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

    async getActivityLogs(skip = 0, limit = 100, userId = null, action = null) {
        const params = new URLSearchParams({ 
            skip: skip,
            limit: limit
        });
        if (userId) {
            params.append('user_id', userId);
        }
        if (action) {
            params.append('action', action);
        }
        return this.request(`/activity-logs?${params}`);
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

    async getAlertThresholds() {
        return this.request('/thresholds/');
    }

    async updateAlertThresholds(thresholds) {
        return this.request('/thresholds/', {
            method: 'PUT',
            body: JSON.stringify(thresholds)
        });
    }

    // Notification methods
    async getNotifications(isArchived = false, skip = 0, limit = 100) {
        const params = new URLSearchParams({ 
            is_archived: isArchived,
            skip: skip,
            limit: limit
        });
        return this.request(`/notifications/?${params}`);
    }

    async markNotificationAsRead(notificationId) {
        return this.request(`/notifications/${notificationId}/read`, {
            method: 'PATCH'
        });
    }

    async archiveNotification(notificationId) {
        return this.request(`/notifications/${notificationId}/archive`, {
            method: 'PATCH'
        });
    }

    async unarchiveNotification(notificationId) {
        return this.request(`/notifications/${notificationId}/unarchive`, {
            method: 'PATCH'
        });
    }
}

// Create a singleton instance
export const apiService = new ApiService();