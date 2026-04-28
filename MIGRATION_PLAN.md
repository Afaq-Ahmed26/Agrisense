# Firestore → PostgreSQL Migration Plan

**Goal**: Replace Firestore data storage with PostgreSQL while keeping Firebase Auth intact.

**Scope**: Backend data persistence layer only. Frontend auth, UI, and API contracts remain unchanged.

**Architecture**:
```
Firebase Auth (unchanged)    → handles user authentication
PostgreSQL (new)            → handles all app data
```

**Cost**: Stays $0/month (Railway free tier PostgreSQL included).

**Estimated Duration**: 4-6 hours of work.

---

## 1. PostgreSQL Schema Design

### A. Users Table (replaces Firestore `users` collection)
```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'farmer',  -- admin, officer, farmer
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    dashboard_preferences JSONB,  -- store as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active),
    INDEX idx_is_deleted (is_deleted)
);
```

### B. Devices Table (replaces Firestore `devices` collection)
```sql
CREATE TABLE devices (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    owner_id VARCHAR(255) NOT NULL,  -- references users.id
    type VARCHAR(100) DEFAULT 'irrigation_device',
    zone_id VARCHAR(255),
    crop_type VARCHAR(100),
    area_size DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_is_active (is_active)
);
```

### C. Device Assignments (replaces embedded `assigned_device_ids` in users)
```sql
CREATE TABLE device_assignments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(255),  -- user who assigned it
    UNIQUE KEY unique_user_device (user_id, device_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_device_id (device_id)
);
```

### D. Sensor Readings Table (replaces Firestore `sensor_readings` collection)
```sql
CREATE TABLE sensor_readings (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    soil_moisture DECIMAL(5, 2),
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    light_level DECIMAL(10, 2),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id_timestamp (device_id, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC)
);
```

### E. Alerts Table (replaces Firestore `alerts` collection)
```sql
CREATE TABLE alerts (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100),  -- low_moisture, high_temp, etc.
    severity VARCHAR(50),  -- critical, warning, info
    message TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_is_acknowledged (is_acknowledged),
    INDEX idx_created_at (created_at DESC)
);
```

### F. Irrigation Schedules Table (replaces Firestore `irrigation_schedules`)
```sql
CREATE TABLE irrigation_schedules (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(50),  -- daily, weekly, monthly
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_is_active (is_active)
);
```

### G. Irrigation Events Table (replaces Firestore `irrigation_events`)
```sql
CREATE TABLE irrigation_events (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_actual_seconds INT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, active, completed, failed
    temperature DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    soil_moisture DECIMAL(5, 2),
    light_level DECIMAL(10, 2),
    user_triggered BOOLEAN DEFAULT FALSE,
    triggered_by VARCHAR(255),  -- user_id if triggered manually
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (triggered_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at DESC)
);
```

### H. Thresholds Table (replaces Firestore `thresholds` collection)
```sql
CREATE TABLE thresholds (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    sensor_type VARCHAR(100),  -- soil_moisture, temperature, humidity, light_level
    min_value DECIMAL(10, 2),
    max_value DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE KEY unique_device_sensor (device_id, sensor_type),
    INDEX idx_device_id (device_id)
);
```

### I. Control States Table (replaces Firestore `control_states`)
```sql
CREATE TABLE control_states (
    device_id VARCHAR(255) PRIMARY KEY,
    mode VARCHAR(50) DEFAULT 'AUTO',  -- AUTO, MANUAL
    pump_state BOOLEAN DEFAULT FALSE,
    threshold DECIMAL(5, 2) DEFAULT 30.0,
    last_change_time TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
```

### J. Activity Logs Table (replaces Firestore `activity_logs`)
```sql
CREATE TABLE activity_logs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    device_id VARCHAR(255),
    action VARCHAR(255),  -- login, device_added, irrigation_started, etc.
    resource_type VARCHAR(100),  -- user, device, irrigation, alert
    resource_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_device_id (device_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at DESC)
);
```

### K. Notifications Table (replaces Firestore `notifications`)
```sql
CREATE TABLE notifications (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    type VARCHAR(100),  -- alert, reminder, system
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at DESC)
);
```

### L. Device Pairing Codes Table (new, for device connection)
```sql
CREATE TABLE device_pairing_codes (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    created_by VARCHAR(255),  -- admin user_id
    claimed_by VARCHAR(255),  -- farmer user_id
    claimed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_expired BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (claimed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_device_id (device_id),
    INDEX idx_code (code),
    INDEX idx_expires_at (expires_at)
);
```

### M. Device OTP Table (new, for OTP verification)
```sql
CREATE TABLE device_otps (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    otp_hash VARCHAR(255) NOT NULL,  -- SHA-256 hashed
    attempts INT DEFAULT 0,
    is_blocked BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    INDEX idx_device_id (device_id),
    INDEX idx_expires_at (expires_at)
);
```

---

## 2. Files to Create (New PostgreSQL Layer)

### A. Database Connection & ORM
- **`backend/app/database.py`** (NEW)
  - SQLAlchemy engine setup
  - Connection pooling
  - Session management
  - Migration utilities

### B. SQLAlchemy Models
- **`backend/app/models/database_models.py`** (NEW)
  - SQLAlchemy ORM definitions for all tables above
  - Relationships defined (User → Devices, Device → Readings, etc.)

### C. Repository/DAO Layer
- **`backend/app/repositories/__init__.py`** (NEW dir)
- **`backend/app/repositories/user_repository.py`** (NEW)
  - CRUD methods: `get_user_by_id`, `get_user_by_email`, `create_user`, `update_user`, `delete_user`, `list_users`
- **`backend/app/repositories/device_repository.py`** (NEW)
  - CRUD methods for devices, device assignments
- **`backend/app/repositories/sensor_repository.py`** (NEW)
  - CRUD for readings, queries (latest by device, date range, aggregates)
- **`backend/app/repositories/alert_repository.py`** (NEW)
  - CRUD for alerts, status queries
- **`backend/app/repositories/irrigation_repository.py`** (NEW)
  - CRUD for schedules and events
- **`backend/app/repositories/threshold_repository.py`** (NEW)
- **`backend/app/repositories/control_state_repository.py`** (NEW)
- **`backend/app/repositories/activity_log_repository.py`** (NEW)
- **`backend/app/repositories/notification_repository.py`** (NEW)
- **`backend/app/repositories/pairing_code_repository.py`** (NEW)
- **`backend/app/repositories/device_otp_repository.py`** (NEW)

---

## 3. Files to Modify (Services Layer → PostgreSQL)

### A. Core Services
- **`backend/app/services/firebase_service.py`**
  - ❌ DELETE (Firestore no longer used)
  - OR ⚠️ REFACTOR to use only Firebase Auth, remove DB access

- **`backend/app/services/mock_firebase_service.py`**
  - ❌ DELETE (no longer needed)

- **`backend/app/services/user_service.py`**
  - Replace: `firebase_service.db` calls → use `user_repository`
  - Replace: `.collection('users').document(...)` → repository methods
  - Keep: Firebase Auth token validation

- **`backend/app/services/sensor_service.py`**
  - Replace: Firestore ops → `sensor_repository`
  - Keep: In-memory caching logic (already optimized)

- **`backend/app/services/alert_service.py`**
  - Replace: Firestore ops → `alert_repository`
  - Keep: Alert evaluation logic

- **`backend/app/services/irrigation_service.py`**
  - Replace: Firestore ops → `irrigation_repository`

- **`backend/app/services/activity_log_service.py`**
  - Replace: Firestore ops → `activity_log_repository`

- **`backend/app/services/notification_service.py`**
  - Replace: Firestore ops → `notification_repository`

- **`backend/app/services/auth_service.py`**
  - ✅ NO CHANGE (Firebase token validation stays the same)

- **`backend/app/services/email_service.py`**
  - ✅ NO CHANGE (OTP email logic stays the same)

- **`backend/app/services/ml_service.py`**
  - ✅ NO CHANGE (ML model logic stays the same)

### B. Dependency Injection
- **`backend/app/dependencies.py`**
  - Add database session provider
  - Add repository instances as dependencies
  - Remove Firebase service injection

---

## 4. Files to Modify (Routes Layer)

All route files need to be updated to use repositories instead of Firestore:

- `backend/app/routes/users.py`
- `backend/app/routes/sensors.py`
- `backend/app/routes/alerts.py`
- `backend/app/routes/irrigation.py`
- `backend/app/routes/thresholds.py`
- `backend/app/routes/activity_logs.py`
- `backend/app/routes/notifications.py`
- `backend/app/routes/auth.py`

**Pattern change**:
```python
# Before
result = await asyncio.to_thread(
    lambda: firebase_service.db.collection('users')
                                 .document(user_id)
                                 .get()
                                 .to_dict()
)

# After
result = await user_repository.get_by_id(user_id)
```

---

## 5. Configuration Changes

### A. Backend Environment Variables (`backend/.env`)
```bash
# Remove these:
# FIREBASE_CONFIG_PATH=...
# FIREBASE_PROJECT_ID=...

# Add PostgreSQL connection:
DATABASE_URL=postgresql://user:password@localhost:5432/agrisense
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false  # Set to true for SQL debugging

# Logging
LOG_LEVEL=INFO
```

### B. Backend Dependencies (`backend/requirements.txt`)
```
# Add:
SQLAlchemy==2.0.x
psycopg2-binary==2.9.x
alembic==1.13.x  # For migrations

# Remove or keep:
firebase-admin  # ONLY if still using Firebase Auth
google-cloud-firestore  # REMOVE
```

### C. Frontend Config (`Frontend/src/config.js`)
```javascript
// NO CHANGE - Frontend still uses Firebase Auth
// Backend API calls still work the same (no breaking changes)
```

---

## 6. Database Migration Setup

### A. Create Alembic Configuration
```bash
cd backend
alembic init migrations
```

### B. Create Migration File
- **`backend/migrations/versions/001_initial_schema.py`**
  - Creates all tables from schema design above
  - Idempotent (safe to run multiple times)

### C. Create Data Migration (if keeping existing Firestore data)
- **`backend/scripts/migrate_firestore_to_postgres.py`** (OPTIONAL)
  - Reads from Firestore (one-time)
  - Writes to PostgreSQL
  - Only needed if you have production data to preserve

---

## 7. Testing Strategy

### A. Unit Tests (`backend/tests/`)
- Test each repository with mock database
- Test service layer with mock repositories
- Existing tests in `backend/test_user_management.py` etc. should still pass

### B. Integration Tests
- Spin up test PostgreSQL (Docker or LocalStack)
- Test end-to-end: API → Service → Repository → Database

### C. Compatibility Tests
- Run existing test suite
- Verify all endpoints return same data structure (API contract unchanged)

---

## 8. Implementation Order (TODO List)

### Phase 1: Foundation
- [ ] Create `backend/app/database.py` with SQLAlchemy setup
- [ ] Create `backend/app/models/database_models.py` with ORM definitions
- [ ] Update `backend/requirements.txt` (add SQLAlchemy, psycopg2, alembic)
- [ ] Update `backend/.env` with DATABASE_URL
- [ ] Initialize Alembic, create migration file

### Phase 2: Repositories
- [ ] Create `backend/app/repositories/` directory structure
- [ ] Create user_repository.py, device_repository.py, sensor_repository.py
- [ ] Create alert_repository.py, irrigation_repository.py
- [ ] Create threshold_repository.py, control_state_repository.py
- [ ] Create activity_log_repository.py, notification_repository.py
- [ ] Create pairing_code_repository.py, device_otp_repository.py

### Phase 3: Services → Repositories
- [ ] Refactor user_service.py (replace Firestore → repository calls)
- [ ] Refactor sensor_service.py
- [ ] Refactor alert_service.py
- [ ] Refactor irrigation_service.py
- [ ] Refactor activity_log_service.py
- [ ] Refactor notification_service.py
- [ ] Refactor firebase_service.py (keep Auth only or delete)

### Phase 4: Routes & Dependencies
- [ ] Update dependencies.py (add repository injection)
- [ ] Update routes/users.py (use repositories)
- [ ] Update routes/sensors.py
- [ ] Update routes/alerts.py
- [ ] Update routes/irrigation.py
- [ ] Update routes/thresholds.py
- [ ] Update routes/activity_logs.py
- [ ] Update routes/notifications.py
- [ ] Update routes/auth.py

### Phase 5: Testing & Validation
- [ ] Run existing tests: `pytest -q`
- [ ] Test signup → verify data in PostgreSQL
- [ ] Test device assignment → verify relationships
- [ ] Test sensor readings → verify pagination + aggregates
- [ ] Test irrigation schedule → verify CRUD operations
- [ ] Test OTP flow end-to-end

### Phase 6: Data Migration (if needed)
- [ ] (Optional) Create migrate_firestore_to_postgres.py
- [ ] Export data from Firestore
- [ ] Import data to PostgreSQL
- [ ] Validate row counts match

### Phase 7: Deployment
- [ ] Create PostgreSQL database on Railway
- [ ] Run migrations: `alembic upgrade head`
- [ ] Deploy backend to Railway
- [ ] Test against production PostgreSQL
- [ ] Switch from Firestore to PostgreSQL (flip in .env)

---

## 9. Notes & Considerations

### A. Backwards Compatibility
- API contracts don't change (same request/response shapes)
- Frontend needs no modifications (uses same API)
- Migration is transparent to end users

### B. Performance
- PostgreSQL queries + indexing → FASTER than Firestore for relational queries
- In-memory caching in sensor_service.py stays (no change)
- Pagination now handled natively in SQL

### C. Quota Concerns (SOLVED)
- PostgreSQL: Pay for storage + compute, not per query
- No more Firestore quota monitoring needed
- Free 1GB on Railway = plenty for AgriSense data

### D. Firestore Clean-up
- After migration proven successful, can delete Firestore database
- Firebase Auth still required (separate free service)

### E. Rollback Plan
- Keep Firestore data alongside PostgreSQL during testing
- If issues found, can revert to Firestore (temporary dual-write strategy)
- Once confident, delete Firestore data

---

## 10. File Change Summary Table

| File | Action | Why |
|------|--------|-----|
| `backend/app/database.py` | CREATE | SQLAlchemy connection pool |
| `backend/app/models/database_models.py` | CREATE | ORM definitions |
| `backend/app/repositories/*` | CREATE | Data access layer (8 files) |
| `backend/app/services/user_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/sensor_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/alert_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/irrigation_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/activity_log_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/notification_service.py` | MODIFY | Replace Firestore calls |
| `backend/app/services/firebase_service.py` | DELETE | No longer needed |
| `backend/app/services/mock_firebase_service.py` | DELETE | No longer needed |
| `backend/app/services/auth_service.py` | NO CHANGE | Firebase Auth stays |
| `backend/app/services/email_service.py` | NO CHANGE | OTP emails stay |
| `backend/app/services/ml_service.py` | NO CHANGE | ML model stays |
| `backend/app/dependencies.py` | MODIFY | Add repository injection |
| `backend/app/routes/*.py` | MODIFY | Use repositories (8 files) |
| `backend/app/middleware/auth.py` | NO CHANGE | JWT validation stays |
| `backend/requirements.txt` | MODIFY | Add SQLAlchemy, psycopg2 |
| `backend/.env` | MODIFY | Add DATABASE_URL |
| `backend/migrations/` | CREATE | Alembic migration system |
| `backend/scripts/migrate_firestore_to_postgres.py` | CREATE (OPTIONAL) | One-time data migration |
| `Frontend/**` | NO CHANGE | Frontend unaffected |

---

## Summary

**Total Files Affected**:
- 8 new repository files (CREATE)
- 3 new infrastructure files (database.py, models, migrations)
- 8 service files modified
- 8 route files modified
- 2 files deleted (firebase_service, mock_firebase_service)
- 2 config files modified
- Frontend: 0 changes

**Effort Estimate**: 4-6 hours

**Risk Level**: Medium (data layer replacement, but well-tested patterns)

**Validation**: All existing tests should pass without modification (API contracts unchanged)

---
