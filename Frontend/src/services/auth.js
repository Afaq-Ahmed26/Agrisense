import {
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    updateProfile,
    sendEmailVerification // Add sendEmailVerification
} from 'firebase/auth';
import { ValidationUtils } from '@/utils/validation';
import { CONFIG } from '@/config';
import { authStore, fetchUser, setUser, logout as storeLogout, isAuthenticated } from '@/store/auth';
import { firebaseService } from './firebase'; // Import firebaseService
import { apiService } from './api'; // Import apiService

// Authentication Service for AgriSense
class AuthService {
    constructor() {
        // Constructor no longer sets up onAuthStateChanged directly.
        // It will be called externally after Firebase is initialized.
    }

    // New method to set up the Firebase Auth state change listener
    listenForAuthStateChanges() {
        if (!firebaseService.auth) {
            console.error("Firebase Auth not initialized when attempting to set auth state listener.");
            return;
        }
        firebaseService.auth.onAuthStateChanged(async (user) => {
            if (user) {
                // User is signed in.
                // It's crucial to await getIdToken() before setting the user to ensure token is available
                setUser(user, await user.getIdToken());
                await fetchUser(); // Fetch detailed user profile from backend using Firebase ID Token
            } else {
                // User is signed out.
                storeLogout();
            }
        });
    }

    // Login method
    async login(email, password) {
        try {
            // Use firebaseService.auth here
            const userCredential = await signInWithEmailAndPassword(firebaseService.auth, email, password);
            // onAuthStateChanged listener will handle setting the user in authStore
            return { success: true, user: userCredential.user, message: 'Login successful' };
        } catch (error) {
            console.error('Firebase Login error:', error);
            // Provide more specific error messages for Firebase Auth errors
            let errorMessage = 'Login failed. Please check your credentials.';
            if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password') {
                errorMessage = 'Invalid email or password.';
            } else if (error.code === 'auth/too-many-requests') {
                errorMessage = 'Too many failed login attempts. Please try again later.';
            }
            return { success: false, message: errorMessage };
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

            // Call backend /register endpoint
            const response = await apiService.register(userData); // Backend returns User object on 200 OK

            if (response && response.id) { // Check if the response is a valid User object (has an ID)
                return { success: true, message: 'Registration successful.' };
            } else {
                // This 'else' block might be hit if the backend returns an empty object or something unexpected on success.
                // However, the backend should always return a User object or throw an error.
                return { success: false, message: response.message || 'Registration failed. Please try again.' };
            }

        } catch (error) {
            console.error('Registration error:', error);
            let errorMessage = 'Registration failed. Please try again.';
            // Improved error message extraction
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message; // Catch generic HTTP errors
            }
            return { success: false, message: errorMessage };
        }
    }

    // Logout method
    async logout() {
        try {
            // Use firebaseService.auth here
            await signOut(firebaseService.auth);
            // onAuthStateChanged listener will handle calling storeLogout()
            return { success: true, message: 'Logged out successfully' };
        } catch (error) {
            console.error('Firebase Logout error:', error);
            return { success: false, message: error.message || 'Logout failed. Please try again.' };
        }
    }

    // Send email verification for account deletion
    async sendDeleteAccountVerificationEmail() {
        try {
            const currentUser = firebaseService.auth.currentUser;
            if (!currentUser) {
                return { success: false, message: 'No user is currently logged in.' };
            }

            // Construct the actionCodeSettings for the verification email
            // This URL will be used to redirect the user after they click the verification link in their email
            // The Firebase console template for email verification needs to be configured to handle this action
            const actionCodeSettings = {
                url: `${window.location.origin}/delete-account-confirm`, // Redirect to a specific page in our app
                handleCodeInApp: true, // This must be true for sendEmailVerification to redirect
            };

            await sendEmailVerification(currentUser, actionCodeSettings);
            return { success: true, message: 'Verification email sent.' };
        } catch (error) {
            console.error('Error sending delete account verification email:', error);
            let errorMessage = error.message || 'Failed to send verification email.';
            if (error.code === 'auth/too-many-requests') {
                errorMessage = 'Too many requests. Please try again later.';
            }
            return { success: false, message: errorMessage };
        }
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