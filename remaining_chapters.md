CHAPTER 5
Graphical User Interfaces

5.1 Introduction
This chapter describes the graphical user interfaces of AgriSense: ML-Powered Smart Irrigation System. It explains how users interact with the system, how screens are structured, how navigation and workflows are executed, how validation is applied, and how role-based access is enforced. The GUI was designed for simplicity, clarity, and practical field use.

5.2 Overall Interface Structure
The AgriSense frontend is implemented using Vue.js with a route-based architecture. The interface is divided into public screens and protected screens. Public screens include Login, Registration, and Forgot Password. Protected screens include Dashboard, Profile, Notifications, Reports, Connect Device, and administrative modules.

The structure includes three layers:
1) Header and navigation layer for module access and user actions.
2) Content layer for widgets, charts, and control panels.
3) Feedback layer for alerts, confirmations, loading states, and validation messages.

[INSERT SCREENSHOT HERE: Overall layout showing top navigation and dashboard workspace]
Figure 5.1: Overall Interface Structure of AgriSense

5.3 Typical Screens Included
The system provides the following major screens for end users and administrators.

Table 5.1: Major GUI Screens in AgriSense
Screen Name | Purpose | Access Level
Login Page | Authenticate users before system access | Public
Registration Page | Create a new user account | Public
Dashboard | Live sensor monitoring and irrigation management | Authenticated
Profile Page | View account details | Authenticated
Update Profile Page | Edit user profile data | Authenticated
Notifications Page | View system notifications and alerts | Authenticated
Reports Page | Show daily, weekly, monthly trend panels | Authenticated
Connect Device Page | Add and display device information | Authenticated
User Management Page | Manage user roles and activation | Admin
Activity Logs Page | Review system and user activities | Admin
Threshold Management Page | Configure system alert thresholds | Admin/Officer

[INSERT SCREENSHOT HERE: Login screen]
Figure 5.2: Login Interface

[INSERT SCREENSHOT HERE: Registration screen]
Figure 5.3: Registration Interface

[INSERT SCREENSHOT HERE: Dashboard screen with widgets]
Figure 5.4: Dashboard Interface

[INSERT SCREENSHOT HERE: Irrigation control panel]
Figure 5.5: Irrigation Control Interface

5.4 Navigation and Workflow Explanation
Navigation is managed through route guards and role-based access checks. Unauthenticated users are redirected to Login. Unauthorized users are redirected away from restricted pages.

5.4.1 Workflow 1: Login to Dashboard
1) User opens the Login page.
2) User enters valid credentials.
3) System verifies authentication.
4) User is redirected to Dashboard.
5) Dashboard begins loading live data and modules.

5.4.2 Workflow 2: Manual Irrigation
1) User opens the Dashboard irrigation module.
2) User selects Manual mode.
3) User enters irrigation duration.
4) User confirms Start action.
5) System sends irrigation request and updates pump status.
6) User may stop irrigation manually or let timer complete.

5.4.3 Workflow 3: ML-Assisted Irrigation
1) System fetches latest sensor values.
2) ML endpoint returns a recommended duration.
3) Recommendation card displays the suggested action.
4) User confirms irrigation trigger.
5) Control state updates and irrigation starts.

5.4.4 Workflow 4: Administrative Management
1) Admin opens User Management page.
2) Admin updates user role or activation status.
3) Admin/Officer opens Threshold Management page.
4) Threshold values are updated and saved.
5) System shows success or error feedback.

[INSERT SCREENSHOT HERE: Workflow collage (Login -> Dashboard -> Trigger -> Confirmation)]
Figure 5.6: Navigation and Action Workflow

5.5 Form Design and Validation
Form design follows data correctness and user feedback principles. Each form uses required fields, input type checks, and validation messages.

5.5.1 Login Form Validation
Email and password are required. Email format is validated. Invalid credentials show an error message.

5.5.2 Registration Form Validation
Full name, email, password, confirm password, and role are required. Passwords must match before submission. Success or error feedback is shown.

5.5.3 Irrigation Control Validation
Manual irrigation duration is bounded. Start and Stop actions are disabled appropriately during loading or active irrigation states.

5.5.4 Threshold Form Validation
Threshold inputs are numeric and accept decimals. Invalid entries are blocked, and save feedback is displayed.

[INSERT SCREENSHOT HERE: Example validation or confirmation message]
Figure 5.7: Form Validation and Confirmation Interface

5.6 Reports and Output Interface
AgriSense provides visual and textual outputs for operational decision making.

1) Live Sensor Output: soil moisture, temperature, humidity, and light values.
2) Irrigation Output: pump state, valve status, and running/idle indicators.
3) Recommendation Output: ML-based irrigation duration and guidance.
4) Notification Output: event confirmations and alerts.
5) Log Output: activity history and audit records.

Table 5.2: Output Interfaces and User Benefits
Output Interface | Description | User Benefit
Sensor Cards | Real-time sensor display | Immediate field awareness
Irrigation Status Panel | Pump and valve state | Better control decisions
ML Recommendation Panel | Predicted duration and advice | Intelligent guidance
Notification Panel | Alerts and confirmations | Faster response
Activity Logs | Historical actions | Transparency and audit

[INSERT SCREENSHOT HERE: Dashboard output showing sensors and irrigation status]
Figure 5.8: Reports and Output Interface

5.7 Role-Based Interfaces
Role-based access control ensures each user sees only relevant modules.

5.7.1 Farmer Interface
Farmers can access Dashboard, Reports, Notifications, Profile, and Connect Device. Administrative pages are hidden.

5.7.2 Officer Interface
Officers have farmer-level access plus threshold configuration permissions.

5.7.3 Admin Interface
Admins have full access, including User Management and Activity Logs.

5.7.4 Access Enforcement
Route guards enforce authentication and role checks. Unauthorized access attempts are redirected to valid screens.

[INSERT SCREENSHOT HERE: Admin user management page]
Figure 5.9: Admin Interface - User Management

[INSERT SCREENSHOT HERE: Threshold configuration page]
Figure 5.10: Officer/Admin Interface - Threshold Management

5.8 Chapter Summary
This chapter documented the GUI structure, navigation, workflows, validation logic, reporting outputs, and role-based access. The interface integrates monitoring, irrigation control, and intelligent recommendations into a single web-based platform suitable for practical field use.

CHAPTER 6
Testing

6.1 Introduction
Testing ensures that AgriSense works correctly across software, cloud, and hardware components. The testing phase verified authentication, sensor data flow, irrigation control, ML prediction flow, API communication, and role-based access. It also evaluated system behavior under network changes and partial sensor availability.

6.2 Testing Objectives
The main objectives were:
1) Verify correctness of frontend and backend modules.
2) Validate end-to-end data flow from ESP32 to dashboard.
3) Confirm safe irrigation workflows in Manual and Auto modes.
4) Ensure authentication and authorization rules are enforced.
5) Identify defects and confirm fixes through regression tests.

6.3 Testing Strategy
The strategy combined manual and automated testing.

6.3.1 Manual Testing
Manual testing validated UI behavior, device communication, irrigation workflows, and role-based access.

6.3.2 Automated Testing
Selective backend tests were executed using pytest to validate user management and API logic.

6.3.3 Black Box Testing
Feature-level checks were executed for login, registration, irrigation trigger/stop, and notification flows.

6.3.4 White Box Testing
Route and service-layer logic were inspected during debugging, especially for ML input validation, mode handling, and failover logic.

6.3.5 Tools Used
Frontend runtime: Vite dev server.
Backend runtime: FastAPI.
API verification: Browser developer tools and console logs.
Test automation: pytest.
Firmware validation: Arduino IDE Serial Monitor.
Data persistence: Firebase/Firestore logs and API responses.

6.4 Test Plan
6.4.1 Features to be Tested
1) Authentication (Login/Register/Logout).
2) User and role management.
3) Live sensor polling.
4) Irrigation start/stop actions.
5) Auto/Manual mode behavior.
6) ML prediction and recommendation flow.
7) Notifications and activity logs.
8) API failover under IP changes.

6.4.2 Testing Approach
1) Module-level verification.
2) API integration testing.
3) End-to-end workflow testing.
4) Regression testing after fixes.

6.4.3 Testing Environment
Hardware: ESP32, soil moisture sensor, DHT22, BH1750, relay module, DC pump.
Software: Vue 3 + Vite, FastAPI + Firebase/Firestore, Arduino IDE, Python ML runtime.
Browser: Google Chrome.
Operating System: Linux development environment.

6.4.4 Test Data and Execution Conditions
Device ID used: esp32-b47cb8.
Sensor transmission interval: approximately 2 seconds.
Dashboard polling interval: 2 seconds.
Control state polling interval: 5 seconds.
Frontend API timeout: 20 seconds.
Failover testing: primary endpoint unreachable, secondary reachable.
ML prediction testing: complete sensor input and partial input (null optional fields).

6.5 Test Cases
Table 6.1: Core Test Cases
ID | Scenario | Input Data | Expected Result | Actual Result | Status
TC-01 | Login with valid credentials | Valid email and password | Redirect to dashboard | Redirected successfully | Pass
TC-02 | Login with invalid password | Valid email, wrong password | Error message shown | Error shown | Pass
TC-03 | Register with valid data | Name, email, password, role | Account created | Account created | Pass
TC-04 | Register with mismatched passwords | Password != confirm | Validation error | Error shown | Pass
TC-05 | Fetch latest sensor reading | Valid device ID | Values displayed | Values displayed | Pass
TC-06 | Trigger manual irrigation | Device ID, duration | Pump starts | Pump starts | Pass
TC-07 | Stop irrigation | Active irrigation | Pump stops | Pump stops | Pass
TC-08 | ML prediction request | Soil moisture + optional fields | Prediction returned | Prediction returned | Pass
TC-09 | Trigger from recommendation | Predicted duration | Trigger succeeds | Trigger succeeds | Pass
TC-10 | Unauthorized admin access | Non-admin user | Redirected | Redirected | Pass
TC-11 | API failover | Primary down | Switch to secondary | Switched | Pass
TC-12 | Sensor disconnected handling | One sensor unplugged | Offline display | Offline display | Pass

[INSERT SCREENSHOT HERE: Test evidence from dashboard and console]
Figure 6.1: Test Execution Evidence

[INSERT SCREENSHOT HERE: Backend terminal/API logs]
Figure 6.2: Backend API Test Logs

[INSERT SCREENSHOT HERE: ESP32 Serial Monitor output]
Figure 6.3: ESP32 Hardware Test Logs

6.6 Test Results and Analysis
Testing confirmed that core functions operate reliably. End-to-end flows from sensor acquisition to dashboard display and irrigation control worked as expected. Authentication and role-based access remained consistent across protected routes.

Result Summary:
Total test cases: 12
Passed: 12
Failed: 0 (after fixes)
Blocked: 0

6.6.1 Analytical Observations
1) Token refresh and route protection remained stable.
2) Sensor-to-dashboard data flow was reliable when wiring and network were stable.
3) Irrigation trigger and stop workflows stabilized after mode-preservation and duration-normalization fixes.
4) Failover improved uptime during IP changes.
5) Partial sensor data was handled safely without system crashes.

6.7 Error Handling and Debugging
Major issues and fixes included:
1) Mode override during irrigation trigger, fixed by preserving control state.
2) ML trigger HTTP 422 errors, fixed by duration normalization.
3) Endpoint instability, fixed by multi-endpoint failover.
4) Optional sensor fields in ML input, fixed by allowing null values.
5) Sensor offline false states, fixed by re-attempting reads in firmware.

6.8 Limitations Found During Testing
1) ML training data is not fully field-specific.
2) Hardware validation was limited to lab-scale setup.
3) Sensor stability depends on wiring and power quality.
4) Network dependency remains a risk in unstable environments.
5) Reports module requires full chart integration.

6.8.1 Recommended Follow-up Actions
1) Build a field dataset with real crop conditions.
2) Validate ML performance across seasons.
3) Standardize sensor wiring and power conditioning.
4) Add offline buffering for network outages.
5) Complete reports visualization and export.

6.9 Chapter Summary
This chapter documented the testing process, environment, test cases, results, debugging, and limitations. The system met its testing objectives and demonstrated stable operation for core use cases with clear pathways for further improvement.

CHAPTER 7
Conclusion and Future Work

7.1 Introduction
This chapter concludes the AgriSense project by summarizing objectives, achievements, and insights from development and testing. It highlights the impact of the system as a smart irrigation prototype and outlines improvements needed for full-scale deployment.

7.2 Summary of Findings and Achievements
The project delivered a complete IoT- and ML-enabled irrigation system integrating ESP32 sensors, cloud services, backend APIs, and a web dashboard. Key achievements include:
1) Real-time sensor acquisition and structured JSON transmission.
2) Secure backend APIs for sensor ingestion, irrigation control, notifications, and logging.
3) A responsive dashboard for monitoring, control, and alerts.
4) Stable manual irrigation control with safe start/stop operations.
5) ML-based recommendation flow integrated into the UI.
6) Role-based access control for admin operations.
7) Failover logic to maintain operation during IP changes.
8) Safe handling of partial sensor availability.

7.2.1 Objective Mapping
The project objectives from Chapter 1 were achieved as follows:
Automated irrigation was implemented through control-state logic and trigger workflows. Live monitoring was implemented through dashboard sensor cards. Intelligent recommendation was implemented through ML prediction integration. User accessibility was ensured through role-based interface design.

7.2.2 Technical Contributions
The system contributes a full pipeline for smart irrigation:
1) Sensor acquisition and preprocessing on ESP32.
2) API-based cloud ingestion and storage.
3) Web dashboard for monitoring and control.
4) ML-based recommendation support.
5) Failover logic for resilient communication.

7.3 Challenges and Limitations
1) ML model trained on public dataset rather than full local field data.
2) Hardware testing limited to lab-scale conditions.
3) Sensor stability depends on wiring and power quality.
4) Network dependency remains a risk in unstable areas.
5) Reports module requires full analytics integration.

7.3.1 Lessons Learned
Hardware reliability is as critical as software logic. Network volatility requires built-in failover. ML accuracy depends on data quality and domain alignment. These lessons emphasize the importance of deployment-focused engineering.

7.4 Future Work and Recommendations
1) Collect field-specific data and retrain the ML model for target crops.
2) Validate model accuracy across seasons and environments.
3) Integrate weather forecast APIs for improved irrigation decisions.
4) Add mobile app support and remote notifications.
5) Implement offline buffering for unreliable connectivity.
6) Complete reports module with charts and export functions.
7) Improve device onboarding and diagnostics.

7.4.1 Prioritized Roadmap (Short-Term)
1) Collect at least one full crop cycle dataset.
2) Retrain and validate the ML model with local data.
3) Finalize reporting charts and export features.
4) Add sensor health diagnostics.

7.4.2 Long-Term Enhancements
1) Multi-farm support with geo-tagged devices.
2) Predictive scheduling based on seasonal patterns.
3) SMS or WhatsApp alerts for low-connectivity users.
4) Mobile app with offline sync.

7.4.3 Deployment Considerations
Production readiness requires maintenance workflows, periodic sensor calibration, and security audits. A field deployment guide should be created for technicians and farmers to ensure correct installation and stable operation.

7.5 Conclusion
AgriSense demonstrates the feasibility of an ML-powered smart irrigation platform that combines IoT sensing, cloud services, and user-centric dashboards. The project achieved its core objectives and delivered a functional prototype with real-time monitoring, irrigation control, and ML-based recommendations. With further field data and deployment-focused improvements, AgriSense can evolve into a robust and scalable solution for water-stressed agricultural regions.
