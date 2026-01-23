import { initializeApp } from "firebase/app";
import { getFirestore, collection, doc, onSnapshot, query, where, orderBy, updateDoc, setDoc, serverTimestamp, getDoc, FieldValue } from "firebase/firestore";
import { getDatabase, ref, onValue, off, update } from "firebase/database";
// ServerValue is accessed via the database object in newer Firebase versions
const ServerValue = {
  TIMESTAMP: { '.sv': 'timestamp' }
};
import { getAuth } from "firebase/auth";
import { CONFIG } from '@/config';

// Firebase Service for AgriSense - handles real-time data communication
class FirebaseService {
    constructor() {
        this.app = null;
        this.db = null; // Firestore
        this.rtdb = null; // Realtime Database
        this.auth = null;
        this.listeners = {}; // Store active listeners
        this.isInitialized = false;
    }

    // Initialize Firebase
    async initialize() {
        if (this.isInitialized) return;

        try {
            // Initialize Firebase app
            this.app = initializeApp(CONFIG.FIREBASE_CONFIG);
            this.db = getFirestore(this.app);
            this.rtdb = getDatabase(this.app);
            this.auth = getAuth(this.app);

            // Note: Persistence is enabled by default in newer Firebase versions
            // The enablePersistence function is not available in ESM builds
            console.info('Firestore persistence is enabled by default');

            this.isInitialized = true;
            console.log('Firebase initialized successfully');
        } catch (error) {
            console.error('Firebase initialization error:', error);
            throw error;
        }
    }

    // Subscribe to sensor data updates
    subscribeToSensorData(deviceId, callback) {
        const path = `devices/${deviceId}/sensors`;
        
        if (this.listeners[path]) {
            this.listeners[path]();
        }

        // Listen to Realtime Database for live updates
        const rtdbRef = ref(this.rtdb, path);
        onValue(rtdbRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                callback(data);
            }
        });

        // Store the unsubscribe function
        this.listeners[path] = () => off(rtdbRef);
    }

    // Subscribe to device status updates
    subscribeToDeviceStatus(deviceId, callback) {
        const path = `devices/${deviceId}/status`;
        
        if (this.listeners[path]) {
            this.listeners[path]();
        }

        const rtdbRef = ref(this.rtdb, path);
        onValue(rtdbRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                callback(data);
            }
        });

        this.listeners[path] = () => off(rtdbRef);
    }

    // Subscribe to irrigation commands
    subscribeToIrrigationCommands(deviceId, callback) {
        const path = `devices/${deviceId}/commands`;
        
        if (this.listeners[path]) {
            this.listeners[path]();
        }

        const rtdbRef = ref(this.rtdb, path);
        onValue(rtdbRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                callback(data);
            }
        });

        this.listeners[path] = () => off(rtdbRef);
    }

    // Subscribe to alerts
    subscribeToAlerts(deviceId, callback) {
        if (!this.db) {
            console.error('Firestore not initialized.');
            return;
        }

        if (!deviceId) {
            // For admin view - listen to all alerts
            const alertsCollection = collection(this.db, 'alerts');
            const alertsQuery = query(
                alertsCollection,
                where('acknowledged', '==', false),
                orderBy('created_at', 'desc')
            );

            if (this.listeners['alerts']) {
                this.listeners['alerts']();
            }

            this.listeners['alerts'] = onSnapshot(alertsQuery, (snapshot) => {
                const alerts = [];
                snapshot.forEach(doc => {
                    alerts.push({ id: doc.id, ...doc.data() });
                });
                callback(alerts);
            });

            return;
        }

        // For specific device alerts
        const path = `devices/${deviceId}/alerts`;
        
        if (this.listeners[path]) {
            this.listeners[path]();
        }

        // Listening to Firestore for alerts
        const alertsCollection = collection(this.db, 'alerts');
        const alertsQuery = query(
            alertsCollection,
            where('device_id', '==', deviceId),
            where('acknowledged', '==', false),
            orderBy('created_at', 'desc')
        );

        this.listeners[path] = onSnapshot(alertsQuery, (snapshot) => {
            const alerts = [];
            snapshot.forEach(doc => {
                alerts.push({ id: doc.id, ...doc.data() });
            });
            callback(alerts);
        });
    }

    // Update irrigation command
    async updateIrrigationCommand(deviceId, command, duration = 0) {
        const path = `devices/${deviceId}/commands`;
        const commandData = {
            irrigation_command: command,
            duration: duration,
            timestamp: ServerValue.TIMESTAMP
        };

        try {
            await update(ref(this.rtdb, path), commandData);
            return { success: true, message: 'Command sent successfully' };
        } catch (error) {
            console.error('Error updating irrigation command:', error);
            return { success: false, message: error.message };
        }
    }

    // Update device status
    async updateDeviceStatus(deviceId, statusUpdate) {
        const path = `devices/${deviceId}/status`;
        const statusData = {
            ...statusUpdate,
            last_seen: ServerValue.TIMESTAMP
        };

        try {
            await update(ref(this.rtdb, path), statusData);
            return { success: true, message: 'Status updated successfully' };
        } catch (error) {
            console.error('Error updating device status:', error);
            return { success: false, message: error.message };
        }
    }

    // Log irrigation event
    async logIrrigationEvent(deviceId, eventData) {
        if (!this.db) {
            console.error('Firestore not initialized.');
            return { success: false, message: 'Firestore not initialized.' };
        }
        try {
            const logCollection = collection(this.db, 'irrigation_logs', deviceId, 'logs');
            const newLogRef = doc(logCollection); // Firestore automatically generates ID

            await setDoc(newLogRef, {
                ...eventData,
                timestamp: serverTimestamp(),
                log_id: newLogRef.id
            });

            return { success: true, logId: newLogRef.id };
        } catch (error) {
            console.error('Error logging irrigation event:', error);
            return { success: false, message: error.message };
        }
    }

    // Acknowledge an alert
    async acknowledgeAlert(alertId, userId) {
        if (!this.db) {
            console.error('Firestore not initialized.');
            return { success: false, message: 'Firestore not initialized.' };
        }
        try {
            const alertRef = doc(this.db, 'alerts', alertId);
            await updateDoc(alertRef, {
                acknowledged: true,
                acknowledged_by: userId,
                acknowledged_at: serverTimestamp()
            });

            return { success: true };
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            return { success: false, message: error.message };
        }
    }

    // Get historical sensor data
    async getHistoricalSensorData(deviceId, startDate, endDate) {
        if (!this.db) {
            console.error('Firestore not initialized.');
            return [];
        }
        try {
            const startTimestamp = startDate ? new Date(startDate).getTime() : Date.now() - (7 * 24 * 60 * 60 * 1000); // Default: last 7 days
            const endTimestamp = endDate ? new Date(endDate).getTime() : Date.now();

            const readingsCollection = collection(this.db, 'sensor_readings', deviceId, 'readings');
            const readingsQuery = query(
                readingsCollection,
                where('timestamp', '>=', startTimestamp),
                where('timestamp', '<=', endTimestamp),
                orderBy('timestamp', 'desc')
            );

            const snapshot = await onSnapshot(readingsQuery); // Using onSnapshot for real-time history or getDocs for one-time fetch
            const readings = [];

            snapshot.forEach(doc => {
                readings.push({ id: doc.id, ...doc.data() });
            });

            return readings.reverse(); // Return in chronological order
        } catch (error) {
            console.error('Error getting historical sensor data:', error);
            throw error;
        }
    }

    // Unsubscribe from all listeners
    unsubscribeAll() {
        Object.values(this.listeners).forEach(unsubscribe => {
            if (typeof unsubscribe === 'function') {
                unsubscribe();
            }
        });
        this.listeners = {};
    }

    // Check if user is signed in
    isUserSignedIn() {
        return this.auth?.currentUser !== null;
    }

    // Get current user
    getCurrentUser() {
        return this.auth?.currentUser;
    }

    // Sign out
    async signOut() {
        try {
            await this.auth.signOut();
            return { success: true };
        } catch (error) {
            console.error('Sign out error:', error);
            return { success: false, message: error.message };
        }
    }

    // Get user role from Firestore
    async getUserRole(userId) {
        if (!this.db) {
            console.error('Firestore not initialized.');
            return null;
        }
        try {
            const userDocRef = doc(this.db, 'users', userId);
            const userDoc = await getDoc(userDocRef);
            if (userDoc.exists()) {
                return userDoc.data().role;
            }
            return null;
        } catch (error) {
            console.error('Error getting user role:', error);
            return null;
        }
    }
}

// Create a singleton instance
export const firebaseService = new FirebaseService();