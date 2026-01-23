import { apiService } from '@/services/api';
import { ValidationUtils } from '@/utils/validation';
import { CONFIG } from '@/config';
import { authStore, fetchUser, setUser, logout as storeLogout, isAuthenticated } from '@/store/auth';

// Authentication Service for AgriSense
class AuthService {
    constructor() {
        // Initialize the user from the store on creation
        this.init();
    }

    // Initialize auth service
    async init() {
        if (isAuthenticated.value) {
            await fetchUser();
        }
    }

    // Login method
    async login(email, password) {
        try {
            const response = await apiService.login(email, password);
            if (response.access_token) {
                setUser(null, response.access_token); // Set token first
                await fetchUser(); // Then fetch the user profile
                return { success: true, user: authStore.user, message: 'Login successful' };
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

            await apiService.register(userData);
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
        } catch (error) {
            console.error('Logout API call failed:', error);
            // We still proceed with local logout
        } finally {
            storeLogout();
        }
        return { success: true, message: 'Logged out successfully' };
    }

    // Check if user is authenticated
    isAuthenticated() {
        return isAuthenticated.value;
    }

    // Get current user
    getCurrentUser() {
        return authStore.user;
    }

    // Get current user role
    getUserRole() {
        return authStore.user?.role || null;
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