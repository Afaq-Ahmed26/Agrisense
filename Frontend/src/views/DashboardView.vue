<template>
  <div>
    <AlertsBanner />
    <div class="container-fluid px-4 mt-3">
      <div class="d-flex justify-content-end mb-3">
        <button class="btn btn-info me-2" @click="$router.push({ name: 'ConnectDevice' })">
          Connect New Device
        </button>
        <button class="btn btn-secondary" @click="toggleCustomizeMode">
          {{ customizeMode ? 'Finish Customizing' : 'Customize Dashboard' }}
        </button>
        <button v-if="customizeMode" class="btn btn-primary ms-2" @click="saveLayout">
          Save Layout
        </button>
      </div>

      <!-- Irrigation Recommendation and Trigger Button -->
      <div v-if="currentDeviceId && irrigationRecommendation" 
           class="card shadow mb-4" 
           :class="recommendationCardClass">
        <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
            <h6 class="m-0 font-weight-bold">Irrigation Recommendation for Device {{ currentDeviceId }}</h6>
        </div>
        <div class="card-body text-center">
            <h4 class="mb-3">{{ irrigationRecommendation.recommendation }}</h4>
            <p v-if="irrigationRecommendation.recommendation === 'Irrigation recommended'" class="lead">
                Reason: Soil moisture ({{ irrigationRecommendation.current_conditions?.soil_moisture }}%) is below the threshold.
            </p>
            <p v-if="irrigationRecommendation.predicted_valve_duration_s > 0" class="mb-3">
                <strong>Predicted Duration:</strong> {{ (irrigationRecommendation.predicted_valve_duration_s / 60).toFixed(1) }} minutes
            </p>
            <button class="btn btn-primary btn-lg" @click="triggerIrrigation" :disabled="showIrrigationSpinner || irrigationRecommendation.recommendation !== 'Irrigation recommended'">
                <span v-if="showIrrigationSpinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span v-else>Trigger Irrigation Now</span>
            </button>
            <p class="mt-3 mb-0 text-muted">
                <small>Last Predicted: {{ new Date(irrigationRecommendation.predicted_at).toLocaleString() }}</small>
            </p>
        </div>
      </div>
      <!-- End Irrigation Recommendation -->

      <div class="row">
        <div class="col-lg-12" v-for="widget in dashboardLayout" :key="widget.id" v-show="widget.visible">
          <div class="position-relative">
            <!-- Ensure components that NEED a device ID only render when it exists -->
            <component 
              v-if="widget.id !== 'PredictionChart' && (widget.id !== 'SensorDisplay' && widget.id !== 'IrrigationControl' || currentDeviceId)"
              :is="getComponent(widget.id)" 
              v-bind="widget.id === 'SensorDisplay' ? { 
                'device-id': currentDeviceId,
                'sensor-data': sensorData || undefined,
                'device-status': deviceStatus || undefined
              } : (widget.id === 'IrrigationControl' ? {
                'device-id': currentDeviceId,
                'external-irrigation-triggered': externalTriggerForIrrigationControl,
                'external-irrigation-duration-seconds': irrigationRecommendation?.predicted_valve_duration_s
              } : (widget.id === 'PredictionChart' ? {
                'device-id': currentDeviceId
              } : {}))"
              @irrigation-started="handleIrrigationStarted"
              @irrigation-stopped="handleIrrigationStopped"
            ></component>
            <button v-if="customizeMode" class="btn btn-danger btn-sm position-absolute top-0 end-0" @click="hideWidget(widget)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <div v-if="customizeMode && hiddenWidgets.length > 0" class="mt-4">
        <h5>Hidden Widgets</h5>
        <ul class="list-group">
          <li v-for="widget in hiddenWidgets" :key="widget.id" class="list-group-item d-flex justify-content-between align-items-center">
            {{ widget.id }}
            <button class="btn btn-success btn-sm" @click="showWidget(widget)">
              <i class="fas fa-plus"></i>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- Irrigation Confirmation Modal -->
    <div class="modal fade" :class="{ 'show d-block': showIrrigationConfirmModal }" tabindex="-1" aria-labelledby="irrigationConfirmModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="irrigationConfirmModalLabel">Confirm Irrigation</h5>
            <button type="button" class="btn-close" @click="showIrrigationConfirmModal = false" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>{{ irrigationActionMessage }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showIrrigationConfirmModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="confirmIrrigation" :disabled="showIrrigationSpinner">
              <span v-if="showIrrigationSpinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <span v-else>Confirm</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue';
import AlertsBanner from '@/components/AlertsBanner.vue';
import SensorDisplay from '@/components/SensorDisplay.vue';
import IrrigationControl from '@/components/IrrigationControl.vue';
import PredictionChart from '@/components/PredictionChart.vue';
import LogsTable from '@/components/LogsTable.vue';
import { authStore, fetchUser } from '@/store/auth';
import { apiService } from '@/services/api';
import { notificationsStore } from '@/store/notifications'; 

const customizeMode = ref(false);
const dashboardLayout = ref([]);
const currentDeviceId = ref(null);
const irrigationRecommendation = ref(null);
const showIrrigationSpinner = ref(false);
const showIrrigationConfirmModal = ref(false);
const irrigationActionMessage = ref('');
const externalTriggerForIrrigationControl = ref(0);
const sensorData = ref(null); // This will hold the latest sensor data
const deviceStatus = ref(null); // This will hold the latest device status
let sensorDataInterval = null; // To store the interval for polling sensor data
let irrigationPending = false; // Guard to prevent infinite irrigation fetch loops
let consecutiveFailures = 0; // For backoff mechanism

const availableWidgets = {
  AlertsBanner: AlertsBanner,
  SensorDisplay: SensorDisplay,
  IrrigationControl: IrrigationControl,
  PredictionChart: PredictionChart,
  LogsTable: LogsTable
};

const defaultLayout = [
  { id: 'AlertsBanner', component: 'AlertsBanner', visible: true, order: 1 },
  { id: 'SensorDisplay', component: 'SensorDisplay', visible: true, order: 2 },
  { id: 'IrrigationControl', component: 'IrrigationControl', visible: true, order: 3 },
  { id: 'PredictionChart', component: 'PredictionChart', visible: true, order: 4 },
  { id: 'LogsTable', component: 'LogsTable', visible: true, order: 5 }
];

// Function to get component by widget ID
const getComponent = (widgetId) => {
  const componentMap = {
    'AlertsBanner': AlertsBanner,
    'SensorDisplay': SensorDisplay,
    'IrrigationControl': IrrigationControl,
    'PredictionChart': PredictionChart,
    'LogsTable': LogsTable
  };
  return componentMap[widgetId] || null;
};

// Function to fetch the latest sensor data from the backend
const fetchLatestSensorData = async (deviceId) => {
  if (!deviceId) {
    sensorData.value = null;
    deviceStatus.value = null;
    return;
  }
  try {
    const data = await apiService.getLatestSensorReadings(deviceId);
    consecutiveFailures = 0;  // reset on success
    sensorData.value = data;
    // Placeholder for device status, as the backend latest-reading only returns SensorReading
    // You might want a separate API for device status or include it in SensorReading if available
    deviceStatus.value = {
      online: true,
      last_heartbeat: data.timestamp, // Use sensor reading timestamp as heartbeat
      battery_level: 100 // Placeholder
    };
  } catch (error) {
    console.error(`Failed to fetch latest sensor data for device ${deviceId}:`, error);
    consecutiveFailures++;
    if (consecutiveFailures >= 3) {
      // Stop hammering — show offline state
      clearInterval(sensorDataInterval);
      console.warn('Backend unreachable, stopping polls');
    }
    // Set default sensor data instead of null to prevent crashes
    sensorData.value = {
      soil_moisture: 0,
      temperature: 0,
      humidity: 0,
      light_level: 0,
      last_updated: new Date().toISOString()
    };
    deviceStatus.value = {
      online: false,
      last_heartbeat: new Date().toISOString(),
      battery_level: 0
    };
  }
};

// Function to set up polling for sensor data
const setupSensorDataPolling = (deviceId) => {
  // 🛑 SAFETY FIRST: Clear ANY existing interval before starting a new one
  if (sensorDataInterval) {
    clearInterval(sensorDataInterval);
    sensorDataInterval = null;
  }

  if (deviceId) {
    // Fetch immediately
    fetchLatestSensorData(deviceId);
    
    // Set up polling every 30 seconds
    // 30,000ms = 30 seconds
    sensorDataInterval = setInterval(() => {
      // Only fetch if the tab is actually visible to the user
      if (!document.hidden) {
        fetchLatestSensorData(deviceId);
      }
    }, 2000); 
    
    console.log(`📡 Started polling for device: ${deviceId} (Interval: 30s)`);
  }
};

// Function to fetch irrigation recommendation
const fetchIrrigationRecommendation = async (deviceId) => {
  if (!deviceId || !sensorData.value) {
    irrigationRecommendation.value = null;
    return;
  }
  try {
    const { soil_moisture, temperature, humidity, light_level } = sensorData.value;
    const prediction = await apiService.getMLPrediction(soil_moisture, temperature, humidity, light_level, deviceId);
    irrigationRecommendation.value = {
      recommendation: prediction.predicted_valve_duration_s > 0 ? "Irrigation recommended" : "No irrigation needed",
      predicted_valve_duration_s: prediction.predicted_valve_duration_s,
      current_conditions: { soil_moisture, temperature, humidity, light_level },
      predicted_at: prediction.predicted_at
    };
  } catch (error) {
    console.error('Failed to fetch irrigation recommendation:', error);
    irrigationRecommendation.value = {
      recommendation: "Error fetching recommendation.",
      predicted_valve_duration_s: 0,
      current_conditions: null,
      predicted_at: new Date().toISOString()
    };
  }
};

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  if (authStore.user && authStore.user.dashboard_preferences) {
    dashboardLayout.value = authStore.user.dashboard_preferences;
  } else {
    dashboardLayout.value = defaultLayout;
  }

  // Fetch devices and set currentDeviceId
  try {
    const devicesResponse = await apiService.getDevices();
    // Ensure devicesResponse is an array before using .find
    const devices = Array.isArray(devicesResponse) ? devicesResponse : [];
    const esp32Device = devices.find(d => d.id === 'esp32-b47cb8');
    
    if (esp32Device) {
      currentDeviceId.value = esp32Device.id;
      console.log('✅ Found ESP32 device, setting as current');
    } else if (devices && devices.length > 0) {
      currentDeviceId.value = devices[0].id;
    } else {
      // Fallback: Use ESP32 device ID if no devices returned
      console.warn('No devices found, using fallback device ID: esp32-b47cb8');
      currentDeviceId.value = 'esp32-b47cb8';
    }
    setupSensorDataPolling(currentDeviceId.value);
  } catch (error) {
    console.error('Failed to fetch devices:', error);
    // Fallback: Use ESP32 device ID on error
    currentDeviceId.value = 'esp32-b47cb8';  // Your actual ESP32 device ID
    setupSensorDataPolling(currentDeviceId.value);
  }
});

// Watch for changes in currentDeviceId to fetch new recommendations and live sensor data
watch(currentDeviceId, (newVal) => {
  if (newVal) {
    setupSensorDataPolling(newVal); // Now sets up polling for API
    // Fetch irrigation recommendation only if sensorData is available
    // A separate watch for sensorData will trigger fetchIrrigationRecommendation
  }
}, { immediate: true });

// Watch for changes in sensorData to fetch new irrigation recommendations
// Guard added to prevent infinite loop when sensorData updates every 5 seconds
// watch(sensorData, async (newVal) => {
//   if (irrigationPending || !newVal || !currentDeviceId.value) return;
  
//   irrigationPending = true;
//   try {
//     await fetchIrrigationRecommendation(currentDeviceId.value);
//   } finally {
//     irrigationPending = false;
//   }
// });

onUnmounted(() => {
  if (sensorDataInterval) {
    clearInterval(sensorDataInterval);
  }
  // Clear any pending irrigation flag
  irrigationPending = false;
});

const toggleCustomizeMode = () => {
  customizeMode.value = !customizeMode.value;
};

const hideWidget = (widget) => {
  widget.visible = false;
};

const showWidget = (widget) => {
  widget.visible = true;
};

const hiddenWidgets = computed(() => {
  return dashboardLayout.value.filter(widget => !widget.visible);
});

const recommendationCardClass = computed(() => {
  if (!irrigationRecommendation.value) {
    return '';
  }
  if (irrigationRecommendation.value.recommendation === 'Irrigation recommended') {
    return 'bg-danger text-white';
  }
  if (irrigationRecommendation.value.recommendation === 'No irrigation needed') {
    return 'bg-success text-white';
  }
  return '';
});

const saveLayout = async () => {
  try {
    await apiService.updateUser(authStore.user.id, { dashboard_preferences: dashboardLayout.value });
    await fetchUser(); // Re-fetch user to update local store
    customizeMode.value = false;
    // Optionally, show a success message
  } catch (error) {
    console.error('Failed to save dashboard layout:', error);
    // Optionally, show an error message
  }
};

const triggerIrrigation = async () => {
  if (!currentDeviceId.value) {
    irrigationActionMessage.value = "Please select a device first.";
    showIrrigationConfirmModal.value = true;
    return;
  }
  if (!irrigationRecommendation.value || irrigationRecommendation.value.predicted_valve_duration_s <= 0) {
    irrigationActionMessage.value = "No irrigation recommended at this time.";
    showIrrigationConfirmModal.value = true;
    return;
  }
  irrigationActionMessage.value = `Are you sure you want to trigger irrigation for ${currentDeviceId.value} for ${(irrigationRecommendation.value.predicted_valve_duration_s / 60).toFixed(1)} minutes?`;
  showIrrigationConfirmModal.value = true;
};

const confirmIrrigation = async () => {
  if (!currentDeviceId.value || !irrigationRecommendation.value) {
    return;
  }
  showIrrigationSpinner.value = true;
  try {
    await apiService.triggerIrrigation(currentDeviceId.value, irrigationRecommendation.value.predicted_valve_duration_s);
    irrigationActionMessage.value = "Irrigation triggered successfully!";
    // Optionally trigger a refresh of logs or status here
  } catch (error) {
    console.error('Failed to trigger irrigation:', error);
    irrigationActionMessage.value = `Failed to trigger irrigation: ${error.message || 'Unknown error'}`;
  } finally {
    showIrrigationSpinner.value = false;
    // Keep modal open to show result, user will close it
    // showIrrigationConfirmModal.value = false; // Close modal after action
    // If successful, trigger the IrrigationControl component to update its state
    if (irrigationActionMessage.value.includes("successfully")) {
      externalTriggerForIrrigationControl.value = Date.now(); // Update to trigger watch
    }
  }
};

const handleIrrigationStarted = (payload) => {
  console.log('Irrigation started event received from IrrigationControl:', payload);
  notificationsStore.addNotification({
    title: 'Irrigation Started',
    message: `Irrigation for device ${payload.deviceId} has started for ${payload.duration} minutes.`,
    type: 'success',
    deviceId: payload.deviceId
  });
};

const handleIrrigationStopped = (payload) => {
  console.log('Irrigation stopped event received from IrrigationControl:', payload);
  notificationsStore.addNotification({
    title: 'Irrigation Stopped',
    message: `Irrigation for device ${payload.deviceId} has completed.`,
    type: 'info',
    deviceId: payload.deviceId
  });
};</script>

<style scoped>
.position-relative {
  padding-top: 2.5rem; /* Add padding to prevent overlap with the remove button */
}
</style>
