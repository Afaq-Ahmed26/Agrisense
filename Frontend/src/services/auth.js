import { auth } from './firebaseConfig';
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    updateProfile
} from 'firebase/auth';
import { ValidationUtils } from '@/utils/validation';
import { CONFIG } from '@/config';
import { authStore, fetchUser, setUser, logout as storeLogout, isAuthenticated } from '@/store/auth';

// Authentication Service for AgriSense
class AuthService {
    constructor() {
        // Initialize the user from the store on creation via Firebase auth state
        onAuthStateChanged(auth, async (user) => {
            if (user) {
                // User is signed in.
                setUser(user, await user.getIdToken()); // Set Firebase user object and token in store
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
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
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

            const userCredential = await createUserWithEmailAndPassword(auth, userData.email, userData.password);
            // Update the user's display name immediately after registration
            if (userData.name && userCredential.user) {
                await updateProfile(userCredential.user, { displayName: userData.name });
            }
            // The onAuthStateChanged listener will handle setting the user in authStore.
            // fetchUser() will then fetch the full profile from backend.

            return { success: true, user: userCredential.user, message: 'Registration successful.' };
        } catch (error) {
            console.error('Firebase Registration error:', error);
            let errorMessage = 'Registration failed. Please try again.';
            if (error.code === 'auth/email-already-in-use') {
                errorMessage = 'The email address is already in use by another account.';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'The email address is not valid.';
            } else if (error.code === 'auth/operation-not-allowed') {
                errorMessage = 'Email/password accounts are not enabled. Please enable in Firebase console.';
            } else if (error.code === 'auth/weak-password') {
                errorMessage = 'The password is too weak.';
            }
            return { success: false, message: errorMessage };
        }
    }

    // Logout method
    async logout() {
        try {
            await signOut(auth);
            // onAuthStateChanged listener will handle calling storeLogout()
            return { success: true, message: 'Logged out successfully' };
        } catch (error) {
            console.error('Firebase Logout error:', error);
            return { success: false, message: error.message || 'Logout failed. Please try again.' };
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