# AgriSense Copilot Instructions

## Build, test, and lint commands

### Frontend (`Frontend/`)
- Install deps: `npm install`
- Run dev server: `npm run dev`
- Production build: `npm run build`
- Preview build: `npm run preview`

### Backend (`backend/`)
- Setup env and deps:
  - `python -m venv venv`
  - `source venv/bin/activate`
  - `pip install -r requirements.txt`
- Start API (project-standard entrypoint): `python start_server.py`
  - Optional simulator mode: `USE_SIMULATOR=true python start_server.py`
- Run tests: `pytest -q`
- Run a single test: `pytest -q test_user_management.py::test_register_user`

### Linting
- No repository lint command is currently configured in `package.json` or backend project files.

## High-level architecture

- **Frontend (Vue 3 + Vite)** in `Frontend/src` uses a service/store split:
  - `services/auth.js` owns Firebase Auth state transitions.
  - `services/api.js` is the single backend client and injects bearer tokens on every request.
  - `store/auth.js` stores `authStore.user` and `accessToken`.
  - `router.js` enforces `requiresAuth` and role-based route guards via `meta.roles`.

- **Backend (FastAPI)** in `backend/app` is route/service layered:
  - `main.py` registers routers by domain (`/auth`, `/users`, `/sensors`, `/irrigation`, `/alerts`, etc.).
  - `middleware/auth.py` (`JWTBearer`) verifies bearer tokens and writes decoded claims to `request.state.user`.
  - Route modules handle HTTP validation/authorization and delegate Firestore logic to `services/*`.
  - Services consistently wrap blocking Firestore SDK calls in `asyncio.to_thread(...)`.

- **Data/auth flow**:
  - Frontend signs users in with Firebase SDK, then sends Firebase ID tokens to FastAPI in `Authorization: Bearer ...`.
  - Backend validates Firebase tokens against Google public keys (`services/auth_service.py`) and uses Firestore for app data.
  - If Firebase Admin credentials are missing, backend falls back to mock Firebase/Firestore (`services/firebase_service.py`) and seeds a default admin user plus `esp32-b47cb8` device.

- **ML component**:
  - Model training script is `model/train_model.py` and outputs `model/irrigation_model.pkl`.
  - Backend `ml_service.py` can load the model, but production-facing ML endpoints in `routes/ml.py` are mostly disabled/commented; only `/ml/status` is active.

## Key conventions in this repository

- **Initialize Firebase before app mount**: frontend startup in `src/main.js` calls `firebaseService.initialize()` before registering auth listeners and mounting Vue.

- **Token freshness is forced**: frontend auth/API flows call `currentUser.getIdToken(true)` (forced refresh), not stale cached JWT assumptions.

- **Auth race avoidance pattern**: API requests wait on `firebaseAuthReadyPromise` (from `services/auth.js`) before issuing authenticated backend requests.

- **Local auth token key is fixed**: frontend persists token under `localStorage["accessToken"]`; reuse this exact key.

- **Backend identity source is request state**: protected routes read identity from `request.state.user` populated by `JWTBearer`, instead of reparsing headers in each route.

- **Mock-first backend fallback is intentional**: missing Firebase credentials should not block development; backend automatically switches to mock services.

- **Current dashboard/device assumption**: frontend dashboard currently prefers device `esp32-b47cb8` and falls back to it when device discovery fails.

- **Irrigation ML path is intentionally stubbed right now**: frontend API methods `getMLPrediction` / `getIrrigationPredictions` return disabled/dummy responses aligned with backend ML route status.
