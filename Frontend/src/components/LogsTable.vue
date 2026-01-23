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
              <th>Water Used (L)</th>
              <th>Mode</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="sortedLogs.length === 0">
              <td colspan="6" class="text-center text-muted">No irrigation logs available.</td>
            </tr>
            <tr v-for="log in sortedLogs" :key="log.id">
              <td>{{ formatDate(log.start_time) }}</td>
              <td>{{ formatTime(log.start_time) }}</td>
              <td>{{ log.duration_minutes }}</td>
              <td>{{ log.water_used_liters }}</td>
              <td>
                <span class="badge" :class="modeClass(log.mode)">{{ capitalize(log.mode) }}</span>
              </td>
              <td>
                <span class="badge" :class="statusClass(log.status)">{{ log.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiService } from '@/services/api';
import { capitalize } from '@/utils/helpers';
import { MAX_LOGS_DISPLAYED } from '@/config';

const deviceId = ref(localStorage.getItem('selectedDeviceId') || 'device_001');
const logs = ref([]);

onMounted(async () => {
  await fetchLogs();
  setInterval(fetchLogs, 30000); // Refresh every 30 seconds
});

const fetchLogs = async () => {
  try {
    const response = await apiService.getIrrigationLogs(deviceId.value, MAX_LOGS_DISPLAYED);
    logs.value = response.logs || [];
  } catch (error) {
    console.error('Error fetching irrigation logs:', error);
    // Optionally, generate sample data for offline/demo mode
    generateSampleLogs();
  }
};

const sortedLogs = computed(() => {
  return [...logs.value].sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
});

const formatDate = (dateString) => new Date(dateString).toLocaleDateString();
const formatTime = (dateString) => new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

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
    // Consider a user-friendly notification here
    console.warn('No logs to export.');
    return;
  }
  let csvContent = 'Start Date,Start Time,Duration (min),Water Used (L),Mode,Status\n';
  sortedLogs.value.forEach(log => {
    const row = [
      formatDate(log.start_time),
      formatTime(log.start_time),
      log.duration_minutes,
      log.water_used_liters,
      log.mode,
      log.status
    ].map(field => `"${field}"`).join(',');
    csvContent += row + '\n';
  });

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', `irrigation_logs_${deviceId.value}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// For offline/demo purposes
const generateSampleLogs = () => {
  logs.value = [
    { id: 1, start_time: new Date(Date.now() - 3600000), duration_minutes: 50, water_used_liters: 500, mode: 'auto', status: 'Completed' },
    { id: 2, start_time: new Date(Date.now() - 86400000), duration_minutes: 30, water_used_liters: 300, mode: 'manual', status: 'Completed' },
    { id: 3, start_time: new Date(Date.now() - 172800000), duration_minutes: 45, water_used_liters: 450, mode: 'auto', status: 'Failed' },
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
