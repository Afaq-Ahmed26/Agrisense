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

        <!-- Mode Selection -->
        <div class="mb-3">
          <strong>Mode:</strong>
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="radio" name="irrigationMode" id="autoMode" value="auto" v-model="mode">
            <label class="form-check-label" for="autoMode">Auto</label>
          </div>
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="radio" name="irrigationMode" id="manualMode" value="manual" v-model="mode">
            <label class="form-check-label" for="manualMode">Manual</label>
          </div>
        </div>

        <!-- Manual Controls -->
        <div id="manualControls" v-if="mode === 'manual'">
          <div class="input-group mb-3">
            <label class="input-group-text" for="durationMinutes">Duration (min)</label>
            <input type="number" class="form-control" id="durationMinutes" v-model.number="durationMinutes" min="1" max="120" :disabled="isRunning || isLoading">
            <button id="startIrrigation" class="btn btn-success" @click="confirmStart" :disabled="isRunning || isLoading">
              <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <i v-else class="fas fa-play"> Start</i>
            </button>
            <button id="stopIrrigation" class="btn btn-danger" @click="confirmStop" :disabled="!isRunning || isLoading">
              <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <i v-else class="fas fa-stop"> Stop</i>
            </button>
          </div>
          <small class="form-text text-muted">Set a duration between 1 and 120 minutes.</small>
        </div>

        <div v-if="countdown" class="mt-2 text-center">
          <p class="h5">{{ countdown }} remaining</p>
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
import { formatDuration } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';
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
const isRunning = ref(false); 
const mode = ref('auto'); 
const durationMinutes = ref(15);
const lastIrrigationTime = ref('N/A');
const countdown = ref('');
let irrigationTimer = null;
let countdownInterval = null;
let pollInterval = null;

const fetchControlState = async () => {
  if (!props.deviceId) return;
  try {
    const state = await apiService.request(`/irrigation/control/${props.deviceId}`, { method: 'GET' });
    mode.value = state.mode.toLowerCase();
    isRunning.value = state.pump_state;
  } catch (error) {
    console.error('Failed to fetch control state:', error);
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
  }
};

const startLocalIrrigationFeedback = (duration) => {
  isRunning.value = true;
  startCountdown(duration);

  irrigationTimer = setTimeout(() => {
    stopIrrigation(true);
  }, duration * 60 * 1000);
};

onMounted(async () => {
  await fetchControlState();
  pollInterval = setInterval(fetchControlState, 5000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
  clearTimers();
});

watch(mode, async (newMode) => {
  await updateControlState({ mode: newMode.toUpperCase() });
});

watch(() => props.externalIrrigationTriggered, (newVal) => {
  if (newVal > 0 && props.externalIrrigationDurationSeconds > 0) {
    const durationMin = Math.ceil(props.externalIrrigationDurationSeconds / 60);
    startLocalIrrigationFeedback(durationMin);
    emit('irrigation-started', { deviceId: props.deviceId, duration: durationMin });
  }
});

const confirmStart = () => {
  if (confirm(`Start irrigation for ${durationMinutes.value} minutes?`)) {
    startIrrigationAPI(durationMinutes.value);
  }
};

const confirmStop = () => {
  if (confirm('Are you sure you want to stop the irrigation?')) {
    stopIrrigation();
  }
};

const startIrrigationAPI = async (duration) => {
  if (!props.deviceId) {
    notificationModal.value.show('No device specified for irrigation.', 'Error', 'error');
    return;
  }
  isLoading.value = true;
  try {
    await updateControlState({ 
      pump_state: true,
      mode: 'MANUAL' 
    });
    
    mode.value = 'manual';
    await apiService.startIrrigation(props.deviceId, duration * 60);
    
    notificationModal.value.show(`Irrigation started for ${duration} minutes!`, 'Success', 'success');
    
    startLocalIrrigationFeedback(duration);
    emit('irrigation-started', { deviceId: props.deviceId, duration: duration });

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

const startCountdown = (minutes) => {
  let seconds = minutes * 60;
  countdown.value = formatDuration(seconds);
  countdownInterval = setInterval(() => {
    seconds--;
    if (seconds >= 0) {
      countdown.value = formatDuration(seconds);
    } else {
      clearTimers();
    }
  }, 1000);
};

const clearTimers = () => {
  clearInterval(countdownInterval);
  clearTimeout(irrigationTimer);
  countdown.value = '';
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
