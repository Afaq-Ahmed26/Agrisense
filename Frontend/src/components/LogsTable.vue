<template>
  <div class="card shadow mb-4">
    <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
      <h6 class="m-0 font-weight-bold text-primary">Recent Irrigation History</h6>
      <div class="dropdown no-arrow">
        <button @click="exportCSV" class="btn btn-sm btn-primary">
          <i class="fas fa-download fa-sm text-white-50"></i> Export CSV
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-bordered" id="dataTable" width="100%" cellspacing="0">
          <thead>
            <tr>
              <th>Date</th>
              <th>Start Time</th>
              <th>Duration (min)</th>
              <th>Water Used ({{ volumeUnit }})</th>
              <th>Mode</th>
              <th>Status</th>
              <th>Temperature ({{ temperatureUnit }})</th>
              <th>Humidity (%)</th>
              <th>Soil Moisture (%)</th>
              <th>Light Level (lx)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="10" class="text-center text-muted">Loading irrigation logs...</td>
            </tr>
            <tr v-else-if="sortedLogs.length === 0">
              <td colspan="10" class="text-center text-muted">No irrigation logs available.</td>
            </tr>
            <template v-else>
              <tr v-for="log in sortedLogs" :key="log.id">
                <td>{{ formatDate(log.start_time) }}</td>
                <td>{{ formatTime(log.start_time) }}</td>
                <td>{{ log.duration_actual_minutes }}</td>
                <td>{{ log.water_used_liters !== null ? formatVolumeWithUserPreferences(log.water_used_liters) : 'N/A' }}</td>
                <td>
                  <span class="badge" :class="modeClass(log.mode)">{{ capitalize(log.mode) }}</span>
                </td>
                <td>
                  <span class="badge" :class="statusClass(log.status)">{{ log.status }}</span>
                </td>
                <td>{{ log.temperature !== null && log.temperature !== undefined ? formatTemperatureWithUserPreferences(log.temperature) : 'N/A' }}</td>
                <td>{{ log.humidity !== null && log.humidity !== undefined ? log.humidity.toFixed(2) : 'N/A' }}</td>
                <td>{{ log.soil_moisture !== null && log.soil_moisture !== undefined ? log.soil_moisture.toFixed(2) : 'N/A' }}</td>
                <td>{{ log.light_level !== null && log.light_level !== undefined ? log.light_level.toFixed(2) : 'N/A' }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { capitalize } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';
import { apiService } from '@/services/api';

const props = defineProps({
  deviceId: {
    type: String,
    default: ''
  },
  refreshKey: {
    type: Number,
    default: 0
  }
});

const logs = ref([]);
const isLoading = ref(false);
let pollInterval = null;

const fetchIrrigationLogs = async () => {
  if (!props.deviceId) {
    logs.value = [];
    return;
  }

  isLoading.value = true;
  try {
    const events = await apiService.getIrrigationLogs(props.deviceId, 100);
    logs.value = (Array.isArray(events) ? events : []).map((event) => {
      const durationActualSeconds = Number(event.duration_actual_seconds ?? 0);
      const durationActualMinutes = Number((durationActualSeconds / 60).toFixed(2));
      const inferredMode = event.mode
        ? String(event.mode).toLowerCase()
        : (event.user_triggered ? 'manual' : 'auto');
      const startTime = event.start_time || event.created_at || null;

      return {
        ...event,
        start_time: startTime,
        mode: inferredMode,
        status: event.status || 'unknown',
        duration_actual_seconds: durationActualSeconds,
        duration_actual_minutes: durationActualMinutes,
        water_used_liters: event.water_used_liters ?? null
      };
    });
  } catch (error) {
    console.error('Failed to fetch irrigation logs:', error);
    logs.value = [];
  } finally {
    isLoading.value = false;
  }
};

onMounted(async () => {
  await fetchIrrigationLogs();
  pollInterval = setInterval(fetchIrrigationLogs, 15000);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});

watch(() => props.deviceId, () => {
  fetchIrrigationLogs();
});

watch(() => props.refreshKey, () => {
  fetchIrrigationLogs();
});

const sortedLogs = computed(() => {
  return [...logs.value].sort((a, b) => new Date(b.start_time || 0) - new Date(a.start_time || 0));
});

const userPrefs = computed(() => authStore.user?.preferences || {
  temperature_unit: 'Celsius',
  volume_unit: 'liters',
  time_zone: 'UTC',
  notification_sound: 'default'
});

const volumeUnit = computed(() => formatWithUserPreferences(0, 'volume', userPrefs.value).unit);
const temperatureUnit = computed(() => formatWithUserPreferences(0, 'temperature', userPrefs.value).unit);

const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleDateString() : 'N/A';
const formatTime = (dateString) => dateString
  ? new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  : 'N/A';

const formatVolumeWithUserPreferences = (liters) => {
  const result = formatWithUserPreferences(liters, 'volume', userPrefs.value);
  return result.formatted;
};

const formatTemperatureWithUserPreferences = (celsius) => {
  const result = formatWithUserPreferences(celsius, 'temperature', userPrefs.value);
  return result.formatted;
};

const normalizeStatus = (status) => String(status || '').toLowerCase();
const normalizeMode = (mode) => String(mode || '').toLowerCase();

const modeClass = (mode) => ({
  'bg-primary': normalizeMode(mode) === 'auto',
  'bg-warning text-dark': normalizeMode(mode) === 'manual'
});

const statusClass = (status) => ({
  'bg-success': normalizeStatus(status).includes('complete') || normalizeStatus(status).includes('stopped'),
  'bg-primary': normalizeStatus(status).includes('active'),
  'bg-danger': normalizeStatus(status).includes('error') || normalizeStatus(status).includes('fail'),
  'bg-secondary': !normalizeStatus(status).includes('complete')
    && !normalizeStatus(status).includes('stopped')
    && !normalizeStatus(status).includes('active')
    && !normalizeStatus(status).includes('error')
    && !normalizeStatus(status).includes('fail')
});

const exportCSV = () => {
  if (logs.value.length === 0) {
    console.warn('No logs to export.');
    return;
  }
  let csvContent = `Start Date,Start Time,Duration (min),Water Used (${volumeUnit.value}),Mode,Status,Temperature (${temperatureUnit.value}),Humidity (%),Soil Moisture (%),Light Level (lx)\n`;
  sortedLogs.value.forEach(log => {
    const row = [
      formatDate(log.start_time),
      formatTime(log.start_time),
      log.duration_actual_minutes,
      formatVolumeWithUserPreferences(log.water_used_liters),
      log.mode,
      log.status,
      log.temperature !== null && log.temperature !== undefined ? formatTemperatureWithUserPreferences(log.temperature) : 'N/A',
      log.humidity !== null && log.humidity !== undefined ? log.humidity.toFixed(2) : 'N/A',
      log.soil_moisture !== null && log.soil_moisture !== undefined ? log.soil_moisture.toFixed(2) : 'N/A',
      log.light_level !== null && log.light_level !== undefined ? log.light_level.toFixed(2) : 'N/A',
    ].map(field => `"${field}"`).join(',');
    csvContent += row + '\n';
  });

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', 'irrigation_logs.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
</script>

<style scoped>
.badge {
  color: white;
}
.text-dark {
  color: #212529 !important;
}
</style>
