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
import { formatDuration } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';

// Simulate a user with permission
const canControlIrrigation = ref(true);

const isRunning = ref(false);
const mode = ref('auto'); // 'auto' or 'manual'
const durationMinutes = ref(15);
const lastIrrigationTime = ref('N/A');
const countdown = ref('');
let irrigationTimer = null;
let countdownInterval = null;

let modalInstance = null;
const modalMessage = ref('');
let confirmedAction = null;

onMounted(() => {
  mode.value = localStorage.getItem('irrigationModePreference') || 'auto';
  const modalEl = document.getElementById('irrigationConfirmationModal');
  if (window.bootstrap && modalEl) {
    modalInstance = new window.bootstrap.Modal(modalEl);
  }
});

watch(mode, (newMode) => {
  localStorage.setItem('irrigationModePreference', newMode);
});

const confirmStart = () => {
  modalMessage.value = `Start irrigation for ${durationMinutes.value} minutes?`;
  confirmedAction = startIrrigation;
  if (modalInstance) modalInstance.show();
};

const confirmStop = () => {
  modalMessage.value = 'Are you sure you want to stop the irrigation?';
  confirmedAction = stopIrrigation;
  if (modalInstance) modalInstance.show();
};

const executeConfirmedAction = () => {
  if (confirmedAction) {
    confirmedAction();
  }
  if (modalInstance) modalInstance.hide();
  confirmedAction = null;
};

const startIrrigation = () => {
  isRunning.value = true;
  startCountdown(durationMinutes.value);

  irrigationTimer = setTimeout(() => {
    stopIrrigation(true); // Automatically stop after duration
  }, durationMinutes.value * 60 * 1000);
};

const stopIrrigation = (wasAutomatic = false) => {
  isRunning.value = false;
  lastIrrigationTime.value = new Date().toLocaleString();
  clearTimers();
  if (!wasAutomatic) {
    // If stopped manually, we might want to show a notification
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

// Function to format volume with user preferences
const formatVolumeWithUserPreferences = (liters) => {
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  const result = formatWithUserPreferences(liters, 'volume', userPrefs);
  return result.formatted;
};
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
