<template>
  <div class="card shadow mb-4">
    <div class="card-header py-3">
      <h6 class="m-0 font-weight-bold text-primary">Irrigation Control</h6>
    </div>
    <div class="card-body">
      <div v-if="!canControlIrrigation" class="text-center text-muted">
        <p>You do not have permission to control irrigation.</p>
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
            <input type="number" class="form-control" id="durationMinutes" v-model.number="durationMinutes" min="1" max="120" :disabled="isRunning">
            <button id="startIrrigation" class="btn btn-success" @click="confirmStart" :disabled="isRunning">
              <i class="fas fa-play"></i> Start
            </button>
            <button id="stopIrrigation" class="btn btn-danger" @click="confirmStop" :disabled="!isRunning">
              <i class="fas fa-stop"></i> Stop
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
import { ref, onMounted, computed, watch } from 'vue';
import { apiService } from '@/services/api';
import { authService } from '@/services/auth';
import { firebaseService } from '@/services/firebase';
import { formatDuration } from '@/utils/helpers';
// Note: Bootstrap's Modal needs to be handled carefully in Vue.
// We'll use the data-bs-toggle attributes in the template, but for showing/hiding programmatically,
// we'd typically need to get the modal instance.
let modalInstance = null;

const deviceId = ref(localStorage.getItem('selectedDeviceId') || 'device_001');
const canControlIrrigation = computed(() => authService.hasPermission('control_own_irrigation'));

const isRunning = ref(false);
const mode = ref('auto'); // 'auto' or 'manual'
const durationMinutes = ref(15);
const lastIrrigationTime = ref('N/A');
const countdown = ref('');
let irrigationTimer = null;
let countdownInterval = null;

// Modal state
const modalMessage = ref('');
let confirmedAction = null;


onMounted(async () => {
  await loadInitialStatus();
  // The listener should be initialized in a higher-level component or service if possible
  // to avoid multiple initializations. For now, we do it here.
  await firebaseService.initialize();
  firebaseService.subscribeToIrrigationStatus(deviceId.value, (status) => {
    updateStatus(status);
  });

  // Get modal instance
  const modalEl = document.getElementById('irrigationConfirmationModal');
  if (window.bootstrap && modalEl) {
    modalInstance = new window.bootstrap.Modal(modalEl);
  }
});

watch(mode, (newMode) => {
  localStorage.setItem('irrigationModePreference', newMode);
  // Potentially send mode change to backend if needed
});

const loadInitialStatus = async () => {
  try {
    const status = await apiService.getIrrigationStatus(deviceId.value);
    updateStatus(status);
    mode.value = localStorage.getItem('irrigationModePreference') || status.mode || 'auto';
  } catch (error) {
    console.error('Failed to load initial irrigation status:', error);
  }
};

const updateStatus = (status) => {
  if (!status) return;
  isRunning.value = status.valve_open || false;
  lastIrrigationTime.value = status.last_irrigation ? new Date(status.last_irrigation).toLocaleString() : 'N/A';

  if (isRunning.value) {
    if (!countdownInterval) {
      // If we don't have start time from backend, we can't show countdown
      // This part needs a robust implementation based on backend data
    }
  } else {
    clearTimers();
  }
};

const confirmStart = () => {
  modalMessage.value = `Start irrigation for ${durationMinutes.value} minutes?`;
  confirmedAction = startIrrigation;
  if(modalInstance) modalInstance.show();
};

const confirmStop = () => {
  modalMessage.value = 'Are you sure you want to stop the irrigation?';
  confirmedAction = stopIrrigation;
  if(modalInstance) modalInstance.show();
};

const executeConfirmedAction = () => {
  if (confirmedAction) {
    confirmedAction();
  }
  if(modalInstance) modalInstance.hide();
  confirmedAction = null;
};

const startIrrigation = async () => {
  try {
    await apiService.startIrrigation(deviceId.value, durationMinutes.value);
    // The firebase listener will update the state to running
    // For immediate feedback, we can optimistically update
    isRunning.value = true;
    startCountdown(durationMinutes.value);
  } catch (error) {
    console.error('Failed to start irrigation:', error);
  }
};

const stopIrrigation = async () => {
  try {
    await apiService.stopIrrigation(deviceId.value);
    // The firebase listener will update the state to stopped
    // For immediate feedback, we can optimistically update
    isRunning.value = false;
    clearTimers();
  } catch (error) {
    console.error('Failed to stop irrigation:', error);
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

// Computed properties for UI display
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
  padding: 0.25em 0.6em;
  border-radius: 0.25rem;
  font-weight: 700;
  font-size: 0.75em;
}
.status-badge.running {
  background-color: #007bff;
  color: white;
}
.status-badge.idle {
  background-color: #6c757d;
  color: white;
}
</style>
