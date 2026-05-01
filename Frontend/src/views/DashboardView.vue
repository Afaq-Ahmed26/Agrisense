<template>
  <div>
    <AlertsBanner />
    <div class="container-fluid px-4 mt-3">
      <div class="d-flex justify-content-end mb-3">
        <button class="btn btn-secondary" @click="toggleCustomizeMode">
          {{ customizeMode ? 'Finish Customizing' : 'Customize Dashboard' }}
        </button>
        <button v-if="customizeMode" class="btn btn-primary ms-2" @click="saveLayout">
          Save Layout
        </button>
      </div>

      <!-- Irrigation Recommendation and Trigger Button -->
      <div v-if="ML_FEATURES_ENABLED && currentDeviceId && irrigationRecommendation" 
           class="card shadow mb-4" 
           :class="recommendationCardClass">
        <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
            <h6 class="m-0 font-weight-bold">Irrigation Recommendation for Device {{ currentDeviceId }}</h6>
        </div>
        <div class="card-body text-center">
            <h4 class="mb-3">{{ irrigationRecommendation.recommendation }}</h4>
            <p v-if="irrigationRecommendation.reason" class="lead">
                Reason: {{ irrigationRecommendation.reason }}
            </p>
            <p v-if="irrigationRecommendation.predicted_valve_duration_s > 0" class="mb-3">
                <strong>Predicted Duration:</strong> {{ irrigationRecommendation.predicted_valve_duration_s }} seconds
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
              v-if="(((widget.id !== 'SensorDisplay' && widget.id !== 'IrrigationControl' && widget.id !== 'PredictionChart') || currentDeviceId) && (ML_FEATURES_ENABLED || widget.id !== 'PredictionChart'))"
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
              } : (widget.id === 'LogsTable' ? {
                'device-id': currentDeviceId,
                'refresh-key': logsRefreshKey
              } : {})))"
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

const ML_FEATURES_ENABLED = true;
const SENSOR_DATA_STALE_MS = 15000;

const customizeMode = ref(false);
const dashboardLayout = ref([]);
const currentDeviceId = ref(null);
const irrigationRecommendation = ref(null);
const showIrrigationSpinner = ref(false);
const showIrrigationConfirmModal = ref(false);
const irrigationActionMessage = ref('');
const externalTriggerForIrrigationControl = ref(0);
const logsRefreshKey = ref(0);
const sensorData = ref(null); // This will hold the latest sensor data
const deviceStatus = ref(null); // This will hold the latest device status
let sensorDataInterval = null; // To store the interval for polling sensor data
let irrigationPending = false; // Guard to prevent infinite irrigation fetch loops
let consecutiveFailures = 0; // For backoff mechanism

const getOfflineSensorData = () => ({
  soil_moisture: null,
  temperature: null,
  humidity: null,
  light_level: null,
  last_updated: null
});

const normalizeApiTimestamp = (value) => {
  if (!value || typeof value !== 'string') return value || null;
  const trimmed = value.trim().replace(' ', 'T');
  const hasTimezone = /([zZ]|[+\-]\d{2}:\d{2})$/.test(trimmed);
  return hasTimezone ? trimmed : `${trimmed}Z`;
};

const normalizeSensorReading = (data) => ({
  ...data,
  last_updated: normalizeApiTimestamp(data?.last_updated || data?.timestamp || null)
});

const isSensorReadingFresh = (reading) => {
  if (!reading?.last_updated) return false;
  const readingTs = new Date(reading.last_updated).getTime();
  return Number.isFinite(readingTs) && (Date.now() - readingTs) <= SENSOR_DATA_STALE_MS;
};

const availableWidgets = {
  AlertsBanner: AlertsBanner,
  SensorDisplay: SensorDisplay,
  IrrigationControl: IrrigationControl,
  PredictionChart: ML_FEATURES_ENABLED ? PredictionChart : null,
  LogsTable: LogsTable
};

const defaultLayout = [
  { id: 'AlertsBanner', component: 'AlertsBanner', visible: true, order: 1 },
  { id: 'SensorDisplay', component: 'SensorDisplay', visible: true, order: 2 },
  { id: 'IrrigationControl', component: 'IrrigationControl', visible: true, order: 3 },
  { id: 'PredictionChart', component: 'PredictionChart', visible: ML_FEATURES_ENABLED, order: 4 },
  { id: 'LogsTable', component: 'LogsTable', visible: true, order: 5 }
];

const mergeDashboardLayout = (savedLayout) => {
  const saved = Array.isArray(savedLayout) ? savedLayout : [];
  const merged = defaultLayout.map((defaults) => {
    const existing = saved.find((item) => item?.id === defaults.id);
    if (!existing) return { ...defaults };

    return {
      ...defaults,
      ...existing,
      id: defaults.id,
      component: defaults.component,
      // Keep logs widget available even if old preferences hid/removed it.
      visible: defaults.id === 'LogsTable' ? true : (existing.visible ?? defaults.visible),
      order: existing.order ?? defaults.order
    };
  });

  return merged.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
};

// Function to get component by widget ID
const getComponent = (widgetId) => {
  const componentMap = {
    'AlertsBanner': AlertsBanner,
    'SensorDisplay': SensorDisplay,
    'IrrigationControl': IrrigationControl,
    'PredictionChart': ML_FEATURES_ENABLED ? PredictionChart : null,
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
    const normalizedData = normalizeSensorReading(data);
    const isFresh = isSensorReadingFresh(normalizedData);

    if (!isFresh) {
      sensorData.value = getOfflineSensorData();
      deviceStatus.value = {
        online: false,
        last_heartbeat: normalizedData.last_updated,
        battery_level: null
      };
      return;
    }

    sensorData.value = normalizedData;
    deviceStatus.value = {
      online: true,
      last_heartbeat: normalizedData.last_updated,
      battery_level: null
    };
  } catch (error) {
    console.error(`Failed to fetch latest sensor data for device ${deviceId}:`, error);
    consecutiveFailures++;
    sensorData.value = getOfflineSensorData();
    deviceStatus.value = {
      online: false,
      last_heartbeat: null,
      battery_level: null
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
    
    // Set up polling every 2 seconds
    // 2000ms = 2 seconds
    sensorDataInterval = setInterval(() => {
      // Only fetch if the tab is actually visible to the user
      if (!document.hidden) {
        fetchLatestSensorData(deviceId);
      }
    }, 2000); 
    
    console.log(`📡 Started polling for device: ${deviceId} (Interval: 2s)`);
  }
};

// Function to fetch irrigation recommendation
const fetchIrrigationRecommendation = async (deviceId) => {
  if (!ML_FEATURES_ENABLED) {
    irrigationRecommendation.value = null;
    return;
  }
  if (!deviceId || !sensorData.value) {
    irrigationRecommendation.value = null;
    return;
  }
  try {
    const { soil_moisture, temperature, humidity, light_level } = sensorData.value;
    if (soil_moisture === null || soil_moisture === undefined) {
      irrigationRecommendation.value = {
        recommendation: "Awaiting soil moisture data.",
        reason: "No soil moisture data available.",
        predicted_valve_duration_s: 0,
        current_conditions: { soil_moisture, temperature, humidity, light_level },
        predicted_at: new Date().toISOString()
      };
      return;
    }

    const thresholds = await apiService.getAlertThresholds();
    const lowThreshold = thresholds.soil_moisture_low || 30.0;

    const prediction = await apiService.getMLPrediction(soil_moisture, temperature, humidity, light_level, deviceId);
    
    let recommendationText = "No irrigation needed";
    let recommendationReason = "";

    // Recommendation logic: only recommend if below low threshold AND ML predicts a need
    if (soil_moisture < lowThreshold && prediction.predicted_valve_duration_s > 0) {
      recommendationText = "Irrigation recommended";
      recommendationReason = `Soil moisture (${soil_moisture}%) is below the low threshold (${lowThreshold}%).`;
    } else {
      recommendationReason = `Soil moisture (${soil_moisture}%) is above the low threshold (${lowThreshold}%).`;
    }

    irrigationRecommendation.value = {
      recommendation: recommendationText,
      reason: recommendationReason,
      predicted_valve_duration_s: prediction.predicted_valve_duration_s,
      current_conditions: { soil_moisture, temperature, humidity, light_level },
      predicted_at: prediction.predicted_at
    };
  } catch (error) {
    console.error('Failed to fetch irrigation recommendation:', error);
    irrigationRecommendation.value = {
      recommendation: "Error fetching recommendation.",
      reason: "Failed to load irrigation recommendation.",
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
  dashboardLayout.value = mergeDashboardLayout(authStore.user?.dashboard_preferences);

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
// Guard added to prevent infinite loop when sensorData updates every 10 seconds
watch(sensorData, async (newVal) => {
  if (!ML_FEATURES_ENABLED || irrigationPending || !newVal || !currentDeviceId.value) return;
  
  irrigationPending = true;
  try {
    await fetchIrrigationRecommendation(currentDeviceId.value);
  } finally {
    irrigationPending = false;
  }
});

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
    // Backend expects an integer number of seconds; round the ML prediction.
    const roundedDurationSeconds = Math.max(1, Math.round(irrigationRecommendation.value.predicted_valve_duration_s || 0));
    await apiService.triggerIrrigation(currentDeviceId.value, roundedDurationSeconds);
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
  logsRefreshKey.value = Date.now();
  const seconds = Number(payload?.durationSeconds);
  const durationText = Number.isFinite(seconds) && seconds > 0
    ? (seconds < 60 ? `${seconds} seconds` : `${(seconds / 60).toFixed(seconds % 60 === 0 ? 0 : 1)} minutes`)
    : `${payload.duration} minutes`;
  notificationsStore.addNotification({
    title: 'Irrigation Started',
    message: `Irrigation for device ${payload.deviceId} has started for ${durationText}.`,
    type: 'success',
    deviceId: payload.deviceId
  });
};

const handleIrrigationStopped = (payload) => {
  console.log('Irrigation stopped event received from IrrigationControl:', payload);
  logsRefreshKey.value = Date.now();
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
