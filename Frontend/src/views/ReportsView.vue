<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h4>Reports</h4>
          </div>
          <div class="card-body">
            <div class="row mb-4">
              <div class="col-md-6">
                <label for="device-select" class="form-label fw-semibold">Device</label>
                <select
                  id="device-select"
                  class="form-select"
                  v-model="selectedDeviceId"
                  :disabled="devicesLoading || devices.length === 0"
                >
                  <option v-if="devices.length === 0" value="">No devices found</option>
                  <option v-for="device in devices" :key="device.id" :value="device.id">
                    {{ device.name || device.id }} ({{ device.id }})
                  </option>
                </select>
              </div>
            </div>

            <div v-if="errorMessage" class="alert alert-danger" role="alert">
              {{ errorMessage }}
            </div>

            <div v-else-if="isLoading" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-3 mb-0">Loading reports...</p>
            </div>

            <div v-else-if="!selectedDeviceId || !hasAnyData" class="text-center py-5 text-muted">
              No data yet for this device.
            </div>

            <div v-else class="row">
              <div class="col-md-12">
                <h5>Daily Trends</h5>
                <div class="chart-container">
                  <canvas ref="dailyCanvas"></canvas>
                </div>
              </div>
              <div class="col-md-12 mt-4">
                <h5>Weekly Trends</h5>
                <div class="chart-container">
                  <canvas ref="weeklyCanvas"></canvas>
                </div>
              </div>
              <div class="col-md-12 mt-4">
                <h5>Monthly Trends</h5>
                <div class="chart-container">
                  <canvas ref="monthlyCanvas"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import Chart from 'chart.js/auto';
import { apiService } from '@/services/api';

const devices = ref([]);
const devicesLoading = ref(false);
const selectedDeviceId = ref('');
const isLoading = ref(false);
const errorMessage = ref('');

const dailyData = ref(null);
const weeklyData = ref(null);
const monthlyData = ref(null);

const dailyCanvas = ref(null);
const weeklyCanvas = ref(null);
const monthlyCanvas = ref(null);

let dailyChart = null;
let weeklyChart = null;
let monthlyChart = null;

const hasAnyData = computed(() => {
  const seriesHasData = (data) => data && (
    (data.soil_moisture || []).some((v) => v !== null) ||
    (data.temperature || []).some((v) => v !== null) ||
    (data.humidity || []).some((v) => v !== null) ||
    (data.light_level || []).some((v) => v !== null)
  );
  return seriesHasData(dailyData.value) || seriesHasData(weeklyData.value) || seriesHasData(monthlyData.value);
});

const chartConfig = (title, labels, data) => ({
  type: 'line',
  data: {
    labels,
    datasets: [
      {
        label: 'Soil Moisture (%)',
        data: data.soil_moisture,
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13,110,253,0.15)',
        tension: 0.3
      },
      {
        label: 'Temperature (°C)',
        data: data.temperature,
        borderColor: '#fd7e14',
        backgroundColor: 'rgba(253,126,20,0.15)',
        tension: 0.3
      },
      {
        label: 'Humidity (%)',
        data: data.humidity,
        borderColor: '#198754',
        backgroundColor: 'rgba(25,135,84,0.15)',
        tension: 0.3
      },
      {
        label: 'Light Level (lx)',
        data: data.light_level,
        borderColor: '#ffc107',
        backgroundColor: 'rgba(255,193,7,0.15)',
        tension: 0.3
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      title: {
        display: false,
        text: title
      },
      legend: {
        position: 'top'
      }
    },
    scales: {
      y: {
        beginAtZero: false
      }
    }
  }
});

const destroyCharts = () => {
  if (dailyChart) {
    dailyChart.destroy();
    dailyChart = null;
  }
  if (weeklyChart) {
    weeklyChart.destroy();
    weeklyChart = null;
  }
  if (monthlyChart) {
    monthlyChart.destroy();
    monthlyChart = null;
  }
};

const renderCharts = async () => {
  destroyCharts();
  await nextTick();

  if (!hasAnyData.value || !dailyCanvas.value || !weeklyCanvas.value || !monthlyCanvas.value) {
    return;
  }

  dailyChart = new Chart(dailyCanvas.value.getContext('2d'), chartConfig('Daily Trends', dailyData.value.labels, dailyData.value));
  weeklyChart = new Chart(weeklyCanvas.value.getContext('2d'), chartConfig('Weekly Trends', weeklyData.value.labels, weeklyData.value));
  monthlyChart = new Chart(monthlyCanvas.value.getContext('2d'), chartConfig('Monthly Trends', monthlyData.value.labels, monthlyData.value));
};

const loadDevices = async () => {
  devicesLoading.value = true;
  try {
    const result = await apiService.getReportDevices();
    const list = Array.isArray(result) ? result : [];
    const seen = new Set();
    devices.value = list.filter((device) => {
      const key = (device?.id || '').trim();
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    if (devices.value.length > 0) {
      selectedDeviceId.value = devices.value[0].id;
    } else {
      selectedDeviceId.value = '';
    }
  } catch (error) {
    errorMessage.value = error.message || 'Failed to load devices.';
  } finally {
    devicesLoading.value = false;
  }
};

const loadReports = async () => {
  if (!selectedDeviceId.value) {
    dailyData.value = null;
    weeklyData.value = null;
    monthlyData.value = null;
    destroyCharts();
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';
  try {
    const [daily, weekly, monthly] = await Promise.all([
      apiService.getReportsDaily(selectedDeviceId.value),
      apiService.getReportsWeekly(selectedDeviceId.value),
      apiService.getReportsMonthly(selectedDeviceId.value)
    ]);
    dailyData.value = daily;
    weeklyData.value = weekly;
    monthlyData.value = monthly;
    await renderCharts();
  } catch (error) {
    destroyCharts();
    errorMessage.value = error.message || 'Failed to load reports.';
  } finally {
    isLoading.value = false;
  }
};

watch(selectedDeviceId, async () => {
  await loadReports();
});

onMounted(async () => {
  await loadDevices();
  await loadReports();
});

onBeforeUnmount(() => {
  destroyCharts();
});
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 320px;
}
</style>
