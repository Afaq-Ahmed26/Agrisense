<template>
  <div class="card shadow mb-4">
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

  <!-- Confirmation Modal -->
  <div class="modal fade" id="irrigationConfirmationModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Confirm Action</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <p>{{ modalMessage }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="button" class="btn btn-primary" @click="executeConfirmedAction">Confirm</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { formatDuration } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';
import { apiService } from '@/services/api'; // Import apiService

const props = defineProps({
  deviceId: {
    type: String,
    default: ''
  },
  // New props for external triggering from DashboardView
  externalIrrigationTriggered: {
    type: Number,
    default: 0
  },
  externalIrrigationDurationSeconds: {
    type: Number,
    default: 0
  }
});

const emit = defineEmits(['irrigation-started', 'irrigation-stopped']); // New emit for events

const isLoading = ref(false);
const isRunning = ref(false); // This will sync with pump_state from backend
const mode = ref('auto'); // Sync with backend mode
const durationMinutes = ref(15);
const lastIrrigationTime = ref('N/A');
const countdown = ref('');
let irrigationTimer = null;
let countdownInterval = null;
let pollInterval = null;

let modalInstance = null;
const modalMessage = ref('');
let confirmedAction = null;

const fetchControlState = async () => {
  if (!props.deviceId) return;
  // Don't set isLoading true for background polling to avoid flicker
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
    // Refresh local state after successful update
    await fetchControlState();
  } catch (error) {
    console.error('Failed to update control state:', error);
  }
};

// Function to manage local state and countdown
const startLocalIrrigationFeedback = (duration) => {
  isRunning.value = true;
  startCountdown(duration);

  irrigationTimer = setTimeout(() => {
    stopIrrigation(true); // Now calls the async stopIrrigation
  }, duration * 60 * 1000);
};

onMounted(async () => {
  await fetchControlState();
  const modalEl = document.getElementById('irrigationConfirmationModal');
  if (window.bootstrap && modalEl) {
    modalInstance = new window.bootstrap.Modal(modalEl);
  }
  // Poll for pump state changes every 5 seconds
  pollInterval = setInterval(fetchControlState, 5000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
  clearTimers();
});

watch(mode, async (newMode) => {
  await updateControlState({ mode: newMode.toUpperCase() });
});

// Watch for external irrigation trigger
watch(() => props.externalIrrigationTriggered, (newVal) => {
  if (newVal > 0 && props.externalIrrigationDurationSeconds > 0) {
    // Convert seconds to minutes for startIrrigation function
    const durationMin = Math.ceil(props.externalIrrigationDurationSeconds / 60);
    // Don't call API again, just start local state management
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

const executeConfirmedAction = () => {
  if (confirmedAction) {
    confirmedAction();
  }
  if (modalInstance) modalInstance.hide();
  confirmedAction = null;
};

// Function to call the API and start local feedback
const startIrrigationAPI = async (duration) => {
  if (!props.deviceId) {
    alert('No device specified for irrigation.');
    return;
  }
  isLoading.value = true;
  try {
    // 1. Update the backend control state to turn pump ON AND set mode to MANUAL
    // This prevents the auto-logic from immediately turning it back off
    await updateControlState({ 
      pump_state: true,
      mode: 'MANUAL' 
    });
    
    // Update local mode state to reflect the change
    mode.value = 'manual';
    
    // 2. Log an event for history/tracking
    await apiService.startIrrigation(props.deviceId, duration * 60);
    
    alert(`Irrigation started for ${duration} minutes!`);
    
    // Start local countdown for visual feedback
    startLocalIrrigationFeedback(duration);
    emit('irrigation-started', { deviceId: props.deviceId, duration: duration });

  } catch (error) {
    console.error('Failed to start irrigation:', error);
    alert('Failed to start irrigation. Check console for details.');
  } finally {
    isLoading.value = false;
  }
};

const stopIrrigation = async (wasAutomatic = false) => {
  isLoading.value = true;
  try {
    // 1. Update backend to turn pump OFF
    await updateControlState({ pump_state: false });
    
    // 2. Tell backend to stop event tracking
    await apiService.stopIrrigation(props.deviceId);

    isRunning.value = false;
    lastIrrigationTime.value = new Date().toLocaleString();
    clearTimers();
    
    if (!wasAutomatic) {
      alert('Irrigation stopped.');
      emit('irrigation-stopped', { deviceId: props.deviceId });
    }
  } catch (error) {
    console.error('Failed to stop irrigation:', error);
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
