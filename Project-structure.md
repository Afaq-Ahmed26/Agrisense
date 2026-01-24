# Project Structure

This document outlines the directory structure of the Agriscense project.

## Top-Level Structure (`tree -L 2`)

```
.
├── backend
│   ├── app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── source
│   ├── start_server.py
│   ├── test_firebase.py
│   ├── venv
│   └── venv,
├── backend.md
├── chotay.md
├── CLAUDE.md
├── Frontend
│   ├── dist
│   ├── Fire-base.md
│   ├── FRONTEND_FEATURES.md
│   ├── index.html
│   ├── mock-server.js
│   ├── node_modules
│   ├── package.json
│   ├── package-lock.json
│   ├── package-mock.json
│   ├── public
│   ├── README.md
│   ├── src
│   └── vite.config.mjs
├── FRONTEND_BACKEND_SETUP.md
├── GEMINI_CONTEXT.md
├── G.md
├── node_modules
│   ├── asynckit
│   ├── axios
│   ├── call-bind-apply-helpers
│   ├── chart.js
│   ├── combined-stream
│   ├── delayed-stream
│   ├── dunder-proto
│   ├── es-define-property
│   ├── es-errors
│   ├── es-object-atoms
│   ├── es-set-tostringtag
│   ├── follow-redirects
│   ├── form-data
│   ├── function-bind
│   ├── get-intrinsic
│   ├── get-proto
│   ├── gopd
│   ├── hasown
│   ├── has-symbols
│   ├── has-tostringtag
│   ├── @kurkle
│   ├── math-intrinsics
│   ├── mime-db
│   ├── mime-types
│   └── proxy-from-env
├── package.json
├── package-lock.json
├── Project-Overview.md
├── Q.md
├── QWEN.md
├── TODAY.md
└── venv
    ├── bin
    ├── include
    ├── lib
    ├── lib64 -> lib
    └── pyvenv.cfg

42 directories, 26 files
```

## Detailed Frontend/src Structure (`ls -R Frontend/src`)

```
Frontend/src:
App.vue  assets  components  config.js  css  main.js  router.js  services  store  utils  views

Frontend/src/assets:
icons  images

Frontend/src/assets/icons:

Frontend/src/assets/images:

Frontend/src/components:
AlertsBanner.vue  IrrigationControl.vue  LogsTable.vue  PredictionChart.vue  SensorDisplay.vue

Frontend/src/css:
dashboard.css  login.css  main.css  register.css

Frontend/src/services:
api.js  auth.js  firebase.js  mock-api.js  mock-data.js

Frontend/src/store:
auth.js

Frontend/src/utils:
helpers.js  validation.js

Frontend/src/views:
DashboardView.vue  ProfileView.vue   ReportsView.vue        UserManagementView.vue
LoginView.vue      RegisterView.vue  UpdateProfileView.vue
```