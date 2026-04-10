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

        this.request = this.request.bind(this); // Bind 'this' to the request method
    }

    // Helper to process the queue of failed requests
    // No longer resolves/rejects the original promises directly,
    // instead, it re-attempts the original requests.
    processQueue(error = null, token = null) {
        this.failedQueue.forEach(req => {
            if (error) {
                req.reject(error);
            } else {
                // If token is successfully refreshed, retry the original request
                const newOptions = { ...req.options };
                newOptions.headers = {
                    ...newOptions.headers,
                    'Authorization': `Bearer ${token}`
                };
                this.request(req.endpoint, newOptions, true)
                    .then(response => req.resolve(response))
                    .catch(err => req.reject(err));
            }
        });
        this.failedQueue = []; // Clear the queue after processing
    }

    // Helper to proactively refresh the token if it's nearing expiration
    async proactiveRefreshToken() {
        const user = firebaseService.auth.currentUser;
        if (user && !this.isRefreshing) {
            const metadata = user.metadata;
            // lastSignInTime and creationTime are in milliseconds since epoch
            // Firebase ID tokens are typically valid for 1 hour (3600 seconds)
            // We'll proactively refresh if it's within 5 minutes (300 seconds) of expiry
            const FIVE_MINUTES = 5 * 60 * 1000; // 5 minutes in milliseconds
            const now = Date.now();

            // getIdTokenResult(true) forces a refresh and gives us access to token details
            const tokenResult = await user.getIdTokenResult(true);
            const expirationTimeMs = tokenResult.expirationTime ? new Date(tokenResult.expirationTime).getTime() : 0;

            if (expirationTimeMs - now < FIVE_MINUTES) {
                console.log("Proactively refreshing token...");
                this.isRefreshing = true;
                try {
                    const refreshedToken = await user.getIdToken(true);
                    setUser(user, refreshedToken);
                    console.log("Token proactively refreshed.");
                } catch (error) {
                    console.error("Proactive token refresh failed:", error);
                    storeLogout();
                } finally {
                    this.isRefreshing = false;
                }
            }
        }
    }

    // Generic API request method with token refresh logic
    async request(endpoint, options = {}, isRetry = false) {
        const url = `${this.baseURL}${endpoint}`;

        // Proactively refresh token before making the request
        if (!isRetry) { // Don't proactively refresh on a retry, to avoid infinite loops if refresh itself fails
            await this.proactiveRefreshToken();
        }

        // Fetch the token *after* proactive refresh (if any) to ensure it's the latest
        const token = localStorage.getItem('accessToken');
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
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

        if (token) {
            requestOptions.headers['Authorization'] = `Bearer ${token}`;
        }

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

                const originalRequest = { endpoint, options, resolve: null, reject: null }; // Store request context

                return new Promise((resolve, reject) => {
                    originalRequest.resolve = resolve;
                    originalRequest.reject = reject;
                    this.failedQueue.push(originalRequest);

                    if (!this.isRefreshing) {
                        this.isRefreshing = true;
                        if (!firebaseService.auth.currentUser) {
                            console.error("Firebase currentUser is null during token refresh attempt. Logging out.");
                            storeLogout();
                            this.processQueue(new Error("No user to refresh token."), null);
                            this.isRefreshing = false; // Reset flag
                            // This reject will propagate to the current request that triggered the refresh
                            originalRequest.reject(new Error("No user to refresh token."));
                            return;
                        }
                        firebaseService.auth.currentUser.getIdToken(true)
                            .then(refreshedToken => {
                                if (firebaseService.auth.currentUser) {
                                    setUser(firebaseService.auth.currentUser, refreshedToken);
                                }
                                this.processQueue(null, refreshedToken); // Process all queued requests
                            })
                            .catch(err => {
                                console.error('Failed to refresh Firebase ID token:', err);
                                this.processQueue(err); // Process all queued requests with error
                                storeLogout(); // Logout if refresh itself fails
                            })
                            .finally(() => {
                                this.isRefreshing = false; // Reset refresh flag
                            });
                    }
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
                console.warn(`🛑 API Timeout [${this.timeout}ms]: ${endpoint}.`);
            } else {
                console.error(`❌ API Request Failed: ${endpoint}`, error.message);
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
        // Force real data for latest readings - no mock fallback
        return this.request(`/sensors/${deviceId}/latest-reading`, {}, false);
    }

    async getSensorHistory(deviceId, startDate, endDate) {
        const params = new URLSearchParams({
            start_time: startDate,
            end_time: endDate
        });
        // Force real data for history - no mock fallback
        return this.request(`/sensors/${deviceId}/readings?${params}`, {}, false);
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

    // async getIrrigationPredictions(deviceId, hoursAhead = 48) {
    //     // Get recommendations for the device
    //     const params = new URLSearchParams({ hours_ahead: hoursAhead });
    //     return this.request(`/ml/future_predictions/${deviceId}?${params}`);
    // }

    // ML model methods
    // async getMLPrediction(soil_moisture, temperature, humidity, light_level, device_id = null) {
    //     try {
    //         const data = { soil_moisture, temperature, humidity, light_level };
    //         if (device_id) {
    //             data.device_id = device_id;
    //         }
    //         return await this.request('/ml/predict', {
    //             method: 'POST',
    //             body: JSON.stringify(data)
    //         });
    //     } catch (error) {
    //         console.warn('ML predict failed, falling back to mock data:', error.message);
    //         const { mockApiService } = await import('@/services/mock-api.js');
    //         return mockApiService.getModelPredictions({ soil_moisture, temperature, humidity, light_level, device_id });
    //     }
    // }

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