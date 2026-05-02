import { CONFIG } from '@/config';
import { firebaseService } from './firebase'; // Import firebaseService
import { logout as storeLogout, setUser } from '@/store/auth'; // Import setUser and storeLogout
import { firebaseAuthReadyPromise } from './auth'; // Import the promise

// API Service for AgriSense - handles all backend communication
class ApiService {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
        this.baseURLs = Array.isArray(CONFIG.API_BASE_URLS) && CONFIG.API_BASE_URLS.length > 0
            ? CONFIG.API_BASE_URLS
            : [this.baseURL];
        this.activeBaseURLIndex = Math.max(0, this.baseURLs.indexOf(this.baseURL));
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



    // Generic API request method with token refresh logic
    async request(endpoint, options = {}, isRetry = false) {
        // Ensure Firebase Auth state is ready before proceeding with authenticated requests.
        // This prevents race conditions where requests are sent before currentUser is populated.
        const tokenFromLocalStorage = localStorage.getItem('accessToken');
        if (tokenFromLocalStorage && !firebaseService.auth.currentUser) {
            console.log("Waiting for Firebase Auth to be ready...");
            await firebaseAuthReadyPromise;
            console.log("Firebase Auth is ready, continuing request.");
        }
        
        // At this point, firebaseService.auth.currentUser should be populated if a user is logged in
        // or confirmed null if no user is logged in.
        
        // Fetch the token *after* Firebase Auth is ready
        let token = null;
        if (firebaseService.auth.currentUser) {
             token = await firebaseService.auth.currentUser.getIdToken(true); // Force refresh token
        } else if (tokenFromLocalStorage) {
            // Fallback for cases where firebase.auth.currentUser might still be null despite `firebaseAuthReadyPromise` resolving,
            // but a token existed in local storage. This ensures we at least send the last known token.
            // This scenario should be rare with firebaseAuthReadyPromise, but provides a safeguard.
            token = tokenFromLocalStorage;
        }

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

        const attemptOrder = this.baseURLs.map((_, idx) => (this.activeBaseURLIndex + idx) % this.baseURLs.length);
        let lastNetworkError = null;

        for (let i = 0; i < attemptOrder.length; i++) {
            const baseIndex = attemptOrder[i];
            const baseURL = this.baseURLs[baseIndex];
            const url = `${baseURL}${endpoint}`;
            let timeoutId = null;

            try {
                const controller = new AbortController();
                timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(url, {
                    ...requestOptions,
                    signal: controller.signal
                });

                if (this.activeBaseURLIndex !== baseIndex) {
                    this.activeBaseURLIndex = baseIndex;
                    this.baseURL = baseURL;
                    console.log(`✅ Switched API endpoint to: ${baseURL}`);
                }

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
                const isNetworkError =
                    error?.name === 'AbortError' ||
                    (typeof error?.message === 'string' &&
                        (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')));

                if (isNetworkError && i < attemptOrder.length - 1) {
                    lastNetworkError = error;
                    console.warn(`⚠️ API endpoint unreachable (${baseURL}), trying next endpoint...`);
                    continue;
                }

                if (error.name === 'AbortError') {
                    console.warn(`🛑 API Timeout [${this.timeout}ms]: ${endpoint}.`);
                } else {
                    console.error(`❌ API Request Failed: ${endpoint}`, error.message);
                }
                throw error;
            } finally {
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
            }
        }

        if (lastNetworkError) {
            throw lastNetworkError;
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

    async generateDevicePairingCode(deviceId, expiresMinutes = 10) {
        return this.request(`/sensors/${deviceId}/pairing-code`, {
            method: 'POST',
            body: JSON.stringify({ expires_minutes: expiresMinutes })
        });
    }

    async claimDevice(deviceId, pairingCode) {
        return this.request(`/sensors/${deviceId}/claim`, {
            method: 'POST',
            body: JSON.stringify({ pairing_code: pairingCode })
        });
    }

    async requestDeviceConnectOtp(deviceId) {
        return this.request(`/sensors/${deviceId}/connect/request-otp`, {
            method: 'POST',
            body: JSON.stringify({})
        });
    }

    async verifyDeviceConnectOtp(deviceId, otp) {
        return this.request(`/sensors/${deviceId}/connect/verify-otp`, {
            method: 'POST',
            body: JSON.stringify({ otp })
        });
    }

    // Irrigation control methods
    async getIrrigationStatus(deviceId) {
        // For now, return a mock status since the backend doesn't have a specific status endpoint
        return { device_id: deviceId, status: 'active', last_updated: new Date().toISOString() };
    }

    async startIrrigation(deviceId, durationSeconds) {
        const normalizedDurationSeconds = Math.max(1, Math.round(Number(durationSeconds)));
        const params = new URLSearchParams({
            device_id: deviceId,
            duration_seconds: normalizedDurationSeconds.toString()
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
        // Call the backend endpoint to stop irrigation - removed trailing slash
        return this.request(`/irrigation/stop/${deviceId}`, {
            method: 'POST'
        });
    }

    async getIrrigationLogs(deviceId, limit = 50) {
        const params = new URLSearchParams({
            device_id: deviceId,
            limit: String(limit)
        });
        return this.request(`/irrigation/events?${params}`, {
            method: 'GET'
        });
    }

    async getIrrigationPredictions(deviceId, hoursAhead = 48) {
        const params = new URLSearchParams({
            hours_ahead: String(hoursAhead)
        });
        return this.request(`/ml/future_predictions/${deviceId}?${params}`, { method: 'GET' });
    }

    async getReportsDaily(deviceId) {
        const params = new URLSearchParams({ device_id: deviceId });
        return this.request(`/reports/daily?${params}`, { method: 'GET' });
    }

    async getReportsWeekly(deviceId) {
        const params = new URLSearchParams({ device_id: deviceId });
        return this.request(`/reports/weekly?${params}`, { method: 'GET' });
    }

    async getReportsMonthly(deviceId) {
        const params = new URLSearchParams({ device_id: deviceId });
        return this.request(`/reports/monthly?${params}`, { method: 'GET' });
    }

    async getReportsCustom(deviceId, startDate, endDate) {
        const params = new URLSearchParams({ 
            device_id: deviceId,
            start_date: startDate,
            end_date: endDate
        });
        return this.request(`/reports/custom?${params}`, { method: 'GET' });
    }

    async exportReportCSV(deviceId, startDate, endDate) {
        const params = new URLSearchParams({ 
            device_id: deviceId,
            start_date: startDate,
            end_date: endDate
        });
        
        // Use standard request to handle token
        const baseURL = this.baseURLs[this.activeBaseURLIndex];
        const url = `${baseURL}/reports/export?${params}`;
        
        const token = await firebaseService.auth.currentUser.getIdToken();
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', `report_${deviceId}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    }

    async getReportDevices() {
        return this.request('/reports/devices', { method: 'GET' });
    }

    // ML model methods
    async getMLPrediction(soil_moisture, temperature, humidity, light_level, device_id = null) {
        return this.request('/ml/predict', {
            method: 'POST',
            body: JSON.stringify({
                soil_moisture,
                temperature,
                humidity,
                light_level,
                device_id
            })
        });
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
        return this.request(`/activity-logs/?${params}`);
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

    async getDefaultAlertThresholds() {
        return this.request('/thresholds/defaults');
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

    // Middleman management methods
    async assignMiddlemanToFarmer(farmerId, middlemanId) {
        return this.request(`/middleman/farmers/${farmerId}/middleman/${middlemanId}`, {
            method: 'POST'
        });
    }

    async revokeMiddlemanFromFarmer(farmerId, middlemanId) {
        return this.request(`/middleman/farmers/${farmerId}/middleman/${middlemanId}`, {
            method: 'DELETE'
        });
    }

    async getMiddlemanForFarmer(farmerId) {
        return this.request(`/middleman/farmer/${farmerId}/middlemen`);
    }

    async getFarmersForMiddleman(middlemanId) {
        return this.request(`/middleman/middleman/${middlemanId}/farmers`);
    }

    async getFarmsForMiddleman(middlemanId) {
        return this.request(`/middleman/middleman/${middlemanId}/farms`);
    }

    // User deletion and recovery methods
    async getDeletedUsers() {
        return this.request('/users/deleted/list');
    }

    async restoreDeletedUser(userId) {
        return this.request(`/users/${userId}/undelete`, {
            method: 'POST'
        });
    }
}

// Create a singleton instance
export const apiService = new ApiService();
