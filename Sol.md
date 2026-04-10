# Gemini response

## Firebase Usage Analysis: Why you are hitting limits quickly

### 1. High-Frequency Frontend Polling (Reads)
The dashboard (`DashboardView.vue`) pulls sensor data from the backend every **10 seconds** (`latest-reading`).
Every time it fetches sensor data, it *immediately* triggers a second request for an ML prediction (`/ml/predict`). 
- **Impact:** 12 API calls per minute per user. Over 24 hours, one open tab generates **~17,280 API calls**. Each call requires token verification and potentially Firestore reads.

### 2. Activity Logging (Writes)
The backend logs almost every user action (login, updating profile, changing preferences, etc.) directly to Firestore via `log_activity`.
- **Impact:** Every single action you perform in the app triggers a guaranteed Firestore write. These are not batched, so 100 actions = 100 writes.

### 3. Alert Generation Logic (Reads/Writes)
When `sensor_data_generator.py` sends data (every 5 minutes per device), the backend evaluates it for alerts. If a reading crosses a threshold (e.g., low moisture):
1.  **Reads** `system_settings/alert_thresholds`.
2.  **Reads** `devices/{device_id}` to find the owner.
3.  **Reads** `notification_preferences/{owner_id}`.
4.  **Writes** a new `alert` document.
5.  **Writes** a new `notification` document.
- **Impact:** Every alert trigger can result in 3-4 reads and 2-3 writes. If your simulated data fluctuates around thresholds, this happens frequently.

### 4. Missing Firestore Indexes
The logs indicate missing composite indexes. When a query fails due to a missing index, the frontend may retry or refresh, multiplying the request volume.

### 5. Inefficient Collection Queries
Functions like `get_devices()` fetch the **entire collection** of devices every time. If your collection grows, every single dashboard load becomes increasingly expensive in terms of reads.

---

## Recommended Optimizations:
1.  **Increase Polling Interval:** Change the 10s poll in `DashboardView.vue` to 30s or 60s.
2.  **Throttle Predictions:** Only request an ML prediction if the sensor data has changed significantly.
3.  **Batch Activity Logs:** Implement a buffer for activity logs to write them in batches of 50 or 100.
4.  **Enhance Caching:** Increase the TTL (Time To Live) for alert thresholds and user preference caches in the backend.
5.  **Implement Pagination:** Use `limit()` on all collection queries.
