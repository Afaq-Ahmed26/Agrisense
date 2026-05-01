<template>
  <div class="card shadow mb-4">
    <NotificationModal ref="notificationModal" />
    <div class="card-header py-3">
      <h6 class="m-0 font-weight-bold text-primary">Irrigation Control</h6>
    </div>
    <div class="card-body">
      <div v-if="!props.deviceId" class="text-center text-muted">
        <p>No device selected for irrigation control.</p>
      </div>

      <div v-else>
        <!-- Status Display -->
        <div class="d-flex justify-content-between align-items-center mb-3">
          <div>
            <strong>Status:</strong>
            <span id="irrigationStatus" :class="statusClass">
              <i :class="statusIcon"></i> {{ irrigationStatus }}
            </span>
          </div>
          <div>
            <strong>Valve:</strong>
            <span id="valveStatus" :class="valveClass">{{ valveStatus }}</span>
          </div>
        </div>

        <!-- ML Prediction Display -->
        <div class="alert alert-info mb-3 py-2" v-if="predictionLiters !== null">
          <div class="d-flex justify-content-between align-items-center">
            <span><i class="fas fa-brain"></i> <strong>Predicted Water Need:</strong></span>
            <span class="badge bg-info text-dark">{{ predictionLiters }} Liters</span>
          </div>
          <small class="text-muted" v-if="predictionSeconds">Duration: {{ formatClock(predictionSeconds) }}</small>
        </div>

        <!-- Mode Selection -->
        <div class="mb-3">
          <strong>Mode:</strong>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="radio"
              name="irrigationMode"
              id="autoMode"
              :checked="mode === 'auto'"
              :disabled="isLoading || isModeChanging"
              @change="handleModeChange('auto')"
            >
            <label class="form-check-label" for="autoMode">Auto</label>
          </div>
          <div class="form-check form-check-inline">
            <input
              class="form-check-input"
              type="radio"
              name="irrigationMode"
              id="manualMode"
              :checked="mode === 'manual'"
              :disabled="isLoading || isModeChanging"
              @change="handleModeChange('manual')"
            >
            <label class="form-check-label" for="manualMode">Manual</label>
          </div>
        </div>

        <!-- Manual Controls -->
        <div id="manualControls" v-if="mode === 'manual'">
          <div class="input-group mb-3">
            <label class="input-group-text" for="durationValue">Duration</label>
            <input
              type="number"
              class="form-control"
              id="durationValue"
              v-model.number="durationValue"
              :min="durationMin"
              :max="durationMax"
              :step="durationStep"
              :disabled="isRunning || isLoading"
            >
            <select class="form-select" v-model="durationUnit" :disabled="isRunning || isLoading" style="max-width: 120px;">
              <option value="minutes">Minutes</option>
              <option value="seconds">Seconds</option>
            </select>
            <button id="startIrrigation" class="btn btn-success" @click="confirmStart" :disabled="isRunning || isLoading">
              <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <i v-else class="fas fa-play"> Start</i>
            </button>
            <button id="stopIrrigation" class="btn btn-danger" @click="confirmStop" :disabled="!isRunning || isLoading">
              <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <i v-else class="fas fa-stop"> Stop</i>
            </button>
          </div>
          <small class="form-text text-muted">Set duration from 0.1-120 minutes or 1-7200 seconds.</small>
        </div>

        <div v-if="countdown" class="mt-2 text-center">
          <p class="h5">{{ countdown }} remaining <small class="text-muted">({{ countdownSeconds }}s)</small></p>
        </div>
      </div>

      <hr>
      <div class="text-xs">
        <strong>Last Irrigation:</strong> <span id="lastIrrigation">{{ lastIrrigationTime }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { apiService } from '@/services/api'; 
import NotificationModal from './NotificationModal.vue';

const props = defineProps({
  deviceId: {
    type: String,
    default: ''
  },
  externalIrrigationTriggered: {
    type: Number,
    default: 0
  },
  externalIrrigationDurationSeconds: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['irrigation-started', 'irrigation-stopped']);

const notificationModal = ref(null);
const isLoading = ref(false);
const isModeChanging = ref(false);
const isRunning = ref(false); 
const mode = ref('auto'); 
const durationUnit = ref('minutes');
const durationValue = ref(15);
const lastIrrigationTime = ref('N/A');
const countdown = ref('');
const countdownSeconds = ref(0);
const predictionLiters = ref(null);
const predictionSeconds = ref(null);
const FLOW_RATE_LPS = 0.05; // 0.05 L/s match backend
let irrigationTimer = null;
let countdownInterval = null;
let pollInterval = null;
let predictionInterval = null;

const durationMin = computed(() => (durationUnit.value === 'seconds' ? 1 : 0.1));
const durationMax = computed(() => (durationUnit.value === 'seconds' ? 7200 : 120));
const durationStep = computed(() => (durationUnit.value === 'seconds' ? 1 : 0.1));

const fetchControlState = async () => {
  if (!props.deviceId) return;
  try {
    const state = await apiService.request(`/irrigation/control/${props.deviceId}`, { method: 'GET' });
    if (!isModeChanging.value && state.mode) {
      mode.value = state.mode.toLowerCase();
    }
    isRunning.value = state.pump_state;
  } catch (error) {
    console.error('Failed to fetch control state:', error);
  }
};

const fetchMLPrediction = async () => {
  if (!props.deviceId) return;
  try {
    const latest = await apiService.getLatestSensorReadings(props.deviceId);
    if (latest && latest.soil_moisture !== undefined) {
      const pred = await apiService.getMLPrediction(
        latest.soil_moisture,
        latest.temperature,
        latest.humidity,
        latest.light_level,
        props.deviceId
      );
      if (pred && pred.predicted_valve_duration_s !== undefined) {
        predictionSeconds.value = pred.predicted_valve_duration_s;
        predictionLiters.value = (pred.predicted_valve_duration_s * FLOW_RATE_LPS).toFixed(2);
      }
    }
  } catch (error) {
    console.warn('Failed to fetch ML prediction for UI:', error);
  }
};

const updateControlState = async (updates) => {
  if (!props.deviceId) return;
  try {
    await apiService.request(`/irrigation/control/${props.deviceId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
    await fetchControlState();
  } catch (error) {
    console.error('Failed to update control state:', error);
    throw error;
  }
};

const startLocalIrrigationFeedback = (durationSeconds) => {
  clearTimers();
  isRunning.value = true;
  startCountdown(durationSeconds);

  irrigationTimer = setTimeout(() => {
    stopIrrigation(true);
  }, durationSeconds * 1000);
};

const formatClock = (totalSeconds) => {
  const normalized = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(normalized / 60);
  const seconds = normalized % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
};

const getDurationSecondsFromInput = (value, unit) => {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return null;
  const seconds = unit === 'seconds' ? Math.round(numericValue) : Math.round(numericValue * 60);
  return Math.max(1, seconds);
};

onMounted(async () => {
  await fetchControlState();
  await fetchMLPrediction();
  pollInterval = setInterval(fetchControlState, 5000);
  predictionInterval = setInterval(fetchMLPrediction, 30000); // Prediction updates every 30s
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
  if (predictionInterval) clearInterval(predictionInterval);
  clearTimers();
});

const handleModeChange = async (newMode) => {
  if (!props.deviceId || mode.value === newMode || isModeChanging.value || isLoading.value) {
    return;
  }

  const previousMode = mode.value;
  mode.value = newMode;
  isModeChanging.value = true;
  try {
    await updateControlState({ mode: newMode.toUpperCase() });
  } catch (error) {
    mode.value = previousMode;
    notificationModal.value?.show('Failed to change irrigation mode.', 'Error', 'error');
  } finally {
    isModeChanging.value = false;
  }
};

watch(() => props.externalIrrigationTriggered, (newVal) => {
  if (newVal > 0 && props.externalIrrigationDurationSeconds > 0) {
    const durationSeconds = Math.max(1, Math.round(props.externalIrrigationDurationSeconds));
    startLocalIrrigationFeedback(durationSeconds);
    emit('irrigation-started', {
      deviceId: props.deviceId,
      durationSeconds,
      duration: durationSeconds / 60
    });
  }
});

watch(durationUnit, (newUnit, oldUnit) => {
  if (newUnit === oldUnit) return;
  const currentValue = Number(durationValue.value);
  if (!Number.isFinite(currentValue)) {
    durationValue.value = newUnit === 'seconds' ? 60 : 1;
    return;
  }

  if (newUnit === 'seconds') {
    durationValue.value = Math.max(1, Math.round(currentValue * 60));
  } else {
    durationValue.value = Math.max(0.1, Number((currentValue / 60).toFixed(1)));
  }
});

const confirmStart = () => {
  const numericDuration = Number(durationValue.value);
  if (!Number.isFinite(numericDuration) || numericDuration < durationMin.value || numericDuration > durationMax.value) {
    notificationModal.value.show(
      `Please enter a valid duration between ${durationMin.value} and ${durationMax.value} ${durationUnit.value}.`,
      'Invalid Duration',
      'error'
    );
    return;
  }

  const durationLabel = durationUnit.value === 'seconds' ? 'seconds' : 'minutes';
  if (confirm(`Start irrigation for ${numericDuration} ${durationLabel}?`)) {
    startIrrigationAPI();
  }
};

const confirmStop = () => {
  if (confirm('Are you sure you want to stop the irrigation?')) {
    stopIrrigation();
  }
};

const startIrrigationAPI = async () => {
  if (!props.deviceId) {
    notificationModal.value.show('No device specified for irrigation.', 'Error', 'error');
    return;
  }
  isLoading.value = true;
  try {
    const durationSeconds = getDurationSecondsFromInput(durationValue.value, durationUnit.value);
    if (durationSeconds === null) {
      throw new Error('Invalid irrigation duration.');
    }
    await updateControlState({ mode: 'MANUAL' });

    mode.value = 'manual';
    await apiService.startIrrigation(props.deviceId, durationSeconds);

    notificationModal.value.show(`Irrigation started for ${durationSeconds} seconds!`, 'Success', 'success');

    startLocalIrrigationFeedback(durationSeconds);
    emit('irrigation-started', {
      deviceId: props.deviceId,
      durationSeconds,
      duration: durationSeconds / 60
    });

  } catch (error) {
    console.error('Failed to start irrigation:', error);
    notificationModal.value.show('Failed to start irrigation. Check console for details.', 'Error', 'error');
  } finally {
    isLoading.value = false;
  }
};

const stopIrrigation = async (wasAutomatic = false) => {
  isLoading.value = true;
  try {
    await updateControlState({ pump_state: false });
    await apiService.stopIrrigation(props.deviceId);

    isRunning.value = false;
    lastIrrigationTime.value = new Date().toLocaleString();
    clearTimers();
    
    if (!wasAutomatic) {
      notificationModal.value.show('Irrigation stopped.', 'Info', 'info');
      emit('irrigation-stopped', { deviceId: props.deviceId });
    }
  } catch (error) {
    console.error('Failed to stop irrigation:', error);
    notificationModal.value.show('Failed to stop irrigation.', 'Error', 'error');
  } finally {
    isLoading.value = false;
  }
};

const startCountdown = (totalSeconds) => {
  let seconds = totalSeconds;
  countdownSeconds.value = seconds;
  countdown.value = formatClock(seconds);
  countdownInterval = setInterval(() => {
    seconds--;
    if (seconds >= 0) {
      countdownSeconds.value = seconds;
      countdown.value = formatClock(seconds);
    } else {
      clearTimers();
    }
  }, 1000);
};

const clearTimers = () => {
  clearInterval(countdownInterval);
  clearTimeout(irrigationTimer);
  countdown.value = '';
  countdownSeconds.value = 0;
  countdownInterval = null;
  irrigationTimer = null;
};

const irrigationStatus = computed(() => isRunning.value ? 'RUNNING' : 'IDLE');
const valveStatus = computed(() => isRunning.value ? 'OPEN' : 'CLOSED');

const statusClass = computed(() => ({
  'status-badge': true,
  'running': isRunning.value,
  'idle': !isRunning.value
}));

const valveClass = computed(() => ({
  'text-success': isRunning.value,
  'text-danger': !isRunning.value
}));

const statusIcon = computed(() => ({
  'fas': true,
  'fa-spinner fa-spin': isRunning.value,
  'fa-pause': !isRunning.value
}));
</script>

<style scoped>
.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-weight: bold;
}
.running {
  background-color: #e6f7ee;
  color: #28a745;
}
.idle {
  background-color: #f8f9fa;
  color: #6c757d;
}
</style>
