import { apiService } from '@/services/api';
import { ValidationUtils } from '@/utils/validation';
import { CONFIG } from '@/config';

// Authentication Service for AgriSense
class AuthService {
    constructor() {
        this.currentUser = null;
    }

    // Initialize auth service
    async init() {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try {
                const response = await apiService.verifyToken();
                if (response.valid) {
                    this.currentUser = response.user;
                    return true;
                }
            } catch (error) {
                console.warn('Token verification failed:', error);
                this.clearAuth();
            }
        }
        return false;
    }

    // Login method
    async login(email, password) {
        try {
            const response = await apiService.login(email, password);
            if (response.access_token) {
                apiService.setToken(response.access_token);

                // Extract user info from the token or create a basic user object
                // For now, we'll create a basic user object
                this.currentUser = {
                    email,
                    role: response.role || 'farmer',
                    id: `user_${Date.now()}` // Generate a temporary ID
                };

                // Store user role in localStorage for quick access
                localStorage.setItem('userRole', this.currentUser.role);

                return { success: true, user: this.currentUser, message: 'Login successful' };
            } else {
                return { success: false, message: 'Invalid response from server' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, message: error.message || 'Login failed. Please try again.' };
        }
    }

    // Register method
    async register(userData) {
        try {
            // Validate password strength using ValidationUtils
            const passwordError = ValidationUtils.password(userData.password);
            if (passwordError) {
                return { success: false, message: passwordError };
            }

            const response = await apiService.register(userData);
            return { success: true, message: 'Registration successful. Please login.' };
        } catch (error) {
            console.error('Registration error:', error);
            return { success: false, message: error.message || 'Registration failed. Please try again.' };
        }
    }

    // Logout method
    async logout() {
        try {
            await apiService.logout();
            this.clearAuth();
            return { success: true, message: 'Logged out successfully' };
        } catch (error) {
            console.error('Logout error:', error);
            this.clearAuth(); // Clear anyway even if API call fails
            return { success: true, message: 'Logged out successfully' };
        }
    }

    // Clear authentication data
    clearAuth() {
        apiService.removeToken();
        this.currentUser = null;
        localStorage.removeItem('userRole');
        localStorage.removeItem('accessToken');
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.currentUser;
    }

    // Get current user role
    getUserRole() {
        return localStorage.getItem('userRole') || null;
    }

    // Check if current user is admin
    isAdmin() {
        return this.getUserRole() === CONFIG.USER_ROLES.ADMIN;
    }

    // Check if current user is middleman
    isMiddleman() {
        return this.getUserRole() === CONFIG.USER_ROLES.MIDDLEMAN;
    }

    // Check if current user is farmer
    isFarmer() {
        return this.getUserRole() === CONFIG.USER_ROLES.FARMER;
    }

    // Check permissions based on role
    hasPermission(permission) {
        const role = this.getUserRole();
        if (!role) return false;

        const permissions = {
            farmer: [
                'view_own_sensors',
                'control_own_irrigation',
                'view_own_logs',
                'manual_override'
            ],
            middleman: [
                'view_assigned_sensors',
                'view_assigned_logs'
            ],
            admin: [
                'view_all_sensors',
                'view_all_users',
                'control_all_irrigation',
                'retrain_model',
                'manage_users',
                'export_data',
                'view_own_sensors',
                'control_own_irrigation',
                'view_own_logs',
                'manual_override'
            ]
        };

        return permissions[role] && permissions[role].includes(permission);
    }
}

// Create a singleton instance
export const authService = new AuthService();