# Firebase Firestore Quota Exhaustion - Root Cause Analysis & Solution

## 1. Problem Overview
The AgriSense application was found to consume an excessive number of Firebase Firestore read requests (approximately 9,000 reads per session start). Over three runs, this resulted in 27,000 reads, quickly exhausting the free tier quota.

## 2. Root Cause Analysis

### A. Non-Paginated Alert Fetching (Primary Cause)
The `AlertsBanner.vue` component calls `apiService.getActiveAlerts()`, which in turn calls the backend endpoint `GET /alerts/`.
- **Backend Issue**: In `backend/app/routes/alerts.py`, the `get_alerts` route calls `alert_service.get_open_alerts()` if no `device_id` is provided. This service method fetches **ALL** open alerts from the Firestore `alerts` collection using `query.stream()` with **no limit**.
- **Frontend Issue**: The `apiService.getActiveAlerts()` method in `Frontend/src/services/api.js` fetches the entire list of alerts and filters them locally by `device_id` and `status`.
- **Impact**: If there are 9,000 unacknowledged/open alerts in the database, every single dashboard load costs **9,000 reads**.

### B. Accumulation of Unique Alert Documents
Alerts are generated in `backend/app/services/alert_service.py` with IDs that include a timestamp:
```python
id=f"alert_{timestamp.timestamp()}_{device_id}_moisture_{current_moisture_severity.value}"
```
- **Issue**: Because every alert has a unique ID including the exact time it was generated, the system creates a new document instead of updating an existing one. If the backend is restarted (clearing the in-memory debounce cache) or if sensors frequently trigger alert conditions, the `alerts` collection grows indefinitely.
- **Impact**: Thousands of "open" alerts accumulate over time, making the non-paginated fetch increasingly expensive.

### C. Unlimited `onSnapshot` Listeners
The `Frontend/src/services/firebase.js` file contains several `onSnapshot` listeners (e.g., `subscribeToLiveSensorData`, `subscribeToAlerts`) that do not use the `limit()` clause.
- **Issue**: When these listeners are initialized, Firestore charges for **every document** currently in the query's result set. Without a limit, a listener on `sensor_readings` or `alerts` will download the entire collection history on the first load.

---

## 3. Proposed Solutions

### 🔴 Immediate Fixes (Required)

#### 1. Implement Server-Side Filtering & Pagination
Modify the backend `get_open_alerts` and `get_device_alerts` methods to always include a `.limit(50)` or similar constraint.
- Update `apiService.getActiveAlerts` in the frontend to pass the `device_id` to the backend so the database query is filtered at the source rather than in the browser.

#### 2. Change Alert ID Generation
Modify `alert_service.py` to use a deterministic ID that doesn't include a high-resolution timestamp for active alerts.
- **Suggested ID**: `f"active_alert_{device_id}_{alert_type}"`.
- This ensures that if a "Low Soil Moisture" alert already exists for a device, it is overwritten or ignored rather than creating a duplicate document.

#### 3. Enforce Limits on Real-time Listeners
Update `Frontend/src/services/firebase.js` to always use `limit(n)` on queries used with `onSnapshot`.
```javascript
const q = query(collectionRef, where(...), orderBy('timestamp', 'desc'), limit(20));
```

### 🟡 Optimization Fixes (Recommended)

#### 4. Increase Polling Intervals
- Increase the notification polling interval in `App.vue` from 3 minutes to 10 or 15 minutes.
- Increase the sensor data polling interval in `DashboardView.vue` from 10 seconds to 30 or 60 seconds.

#### 5. Backend User Caching
Implement in-memory caching for `get_user_from_firestore` in `user_service.py`. Currently, almost every authenticated request triggers a Firestore read to verify the user's role.

#### 6. Database Cleanup
Run a cleanup script (like `backend/cleanup_firestore.py`) to delete or archive the thousands of old unacknowledged alerts and sensor readings that are no longer needed for live operations.
