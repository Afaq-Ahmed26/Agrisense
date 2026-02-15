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
            <tr v-if="sortedLogs.length === 0">
              <td colspan="10" class="text-center text-muted">No irrigation logs available.</td>
            </tr>
            <tr v-for="log in sortedLogs" :key="log.id">
              <td>{{ formatDate(log.start_time) }}</td>
              <td>{{ formatTime(log.start_time) }}</td>
              <td>{{ log.duration_actual_minutes }}</td>
              <td>{{ formatVolumeWithUserPreferences(log.water_used_liters) }}</td>
              <td>
                <span class="badge" :class="modeClass(log.mode)">{{ capitalize(log.mode) }}</span>
              </td>
              <td>
                <span class="badge" :class="statusClass(log.status)">{{ log.status }}</span>
              </td>
              <td>{{ log.temperature ? formatTemperatureWithUserPreferences(log.temperature) : 'N/A' }}</td>
              <td>{{ log.humidity ? log.humidity.toFixed(2) : 'N/A' }}</td>
              <td>{{ log.soil_moisture ? log.soil_moisture.toFixed(2) : 'N/A' }}</td>
              <td>{{ log.light_level ? log.light_level.toFixed(2) : 'N/A' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { capitalize } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';

const logs = ref([]);

onMounted(() => {
  generateSampleLogs();
});

const sortedLogs = computed(() => {
  return [...logs.value].sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
});

const userPrefs = computed(() => authStore.user?.preferences || {
  temperature_unit: 'Celsius',
  volume_unit: 'liters',
  time_zone: 'UTC',
  notification_sound: 'default'
});

const volumeUnit = computed(() => formatWithUserPreferences(0, 'volume', userPrefs.value).unit);
const temperatureUnit = computed(() => formatWithUserPreferences(0, 'temperature', userPrefs.value).unit);

const formatDate = (dateString) => new Date(dateString).toLocaleDateString();
const formatTime = (dateString) => new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

const formatVolumeWithUserPreferences = (liters) => {
  const result = formatWithUserPreferences(liters, 'volume', userPrefs.value);
  return result.formatted;
};

const formatTemperatureWithUserPreferences = (celsius) => {
  const result = formatWithUserPreferences(celsius, 'temperature', userPrefs.value);
  return result.formatted;
};

const modeClass = (mode) => ({
  'bg-primary': mode?.toLowerCase() === 'auto',
  'bg-warning text-dark': mode?.toLowerCase() === 'manual'
});

const statusClass = (status) => ({
  'bg-success': status?.toLowerCase().includes('complete'),
  'bg-danger': status?.toLowerCase().includes('error') || status?.toLowerCase().includes('fail'),
  'bg-secondary': !status?.toLowerCase().includes('complete') && !status?.toLowerCase().includes('error')
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
      log.temperature ? formatTemperatureWithUserPreferences(log.temperature) : 'N/A',
      log.humidity ? log.humidity.toFixed(2) : 'N/A',
      log.soil_moisture ? log.soil_moisture.toFixed(2) : 'N/A',
      log.light_level ? log.light_level.toFixed(2) : 'N/A',
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

const generateSampleLogs = () => {
  logs.value = [
    { id: 1, start_time: new Date(Date.now() - 3600000), duration_actual_minutes: 50, water_used_liters: 500, mode: 'auto', status: 'Completed', temperature: 25.5, humidity: 60.2, soil_moisture: 45.1, light_level: 800 },
    { id: 2, start_time: new Date(Date.now() - 86400000), duration_actual_minutes: 30, water_used_liters: 300, mode: 'manual', status: 'Completed', temperature: 24.1, humidity: 62.5, soil_moisture: 40.7, light_level: 750 },
    { id: 3, start_time: new Date(Date.now() - 172800000), duration_actual_minutes: 45, water_used_liters: 450, mode: 'auto', status: 'Failed', temperature: 26.8, humidity: 58.9, soil_moisture: 50.3, light_level: 850 },
  ];
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
