<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card shadow">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h4 class="mb-0">Historical Reports</h4>
            <button class="btn btn-sm btn-light" @click="handleExport" :disabled="!selectedDeviceId || isLoading">
              <i class="fas fa-file-export"></i> Export CSV
            </button>
          </div>
          <div class="card-body">
            <!-- Filters Row -->
            <div class="row mb-4 align-items-end">
              <div class="col-md-3">
                <label for="device-select" class="form-label fw-bold">Device</label>
                <select id="device-select" class="form-select" v-model="selectedDeviceId" :disabled="devicesLoading">
                  <option v-for="device in devices" :key="device.id" :value="device.id">
                    {{ device.name || device.id }}
                  </option>
                </select>
              </div>
              
              <div class="col-md-3">
                <label for="range-select" class="form-label fw-bold">Range</label>
                <select id="range-select" class="form-select" v-model="rangeSelection">
                  <option value="daily">Last 24 Hours</option>
                  <option value="weekly">Last 7 Days</option>
                  <option value="monthly">Last 30 Days</option>
                  <option value="custom">Custom Range</option>
                </select>
              </div>

              <template v-if="rangeSelection === 'custom'">
                <div class="col-md-2">
                  <label for="start-date" class="form-label fw-bold">From</label>
                  <input type="date" id="start-date" class="form-control" v-model="startDate">
                </div>
                <div class="col-md-2">
                  <label for="end-date" class="form-label fw-bold">To</label>
                  <input type="date" id="end-date" class="form-control" v-model="endDate">
                </div>
              </template>
              
              <div class="col-md-2">
                <button class="btn btn-primary w-100" @click="loadReports" :disabled="isLoading">
                  <i class="fas fa-sync"></i> Refresh
                </button>
              </div>
            </div>

            <!-- Data Type Selector -->
            <div class="mb-4">
              <label class="form-label fw-bold d-block">Display Data Types</label>
              <div class="btn-group" role="group">
                <input type="checkbox" class="btn-check" id="btn-soil" v-model="visibleTypes.soil" autocomplete="off">
                <label class="btn btn-outline-primary" for="btn-soil">Soil Moisture</label>

                <input type="checkbox" class="btn-check" id="btn-temp" v-model="visibleTypes.temp" autocomplete="off">
                <label class="btn btn-outline-warning" for="btn-temp">Temperature</label>

                <input type="checkbox" class="btn-check" id="btn-hum" v-model="visibleTypes.hum" autocomplete="off">
                <label class="btn btn-outline-success" for="btn-hum">Humidity</label>

                <input type="checkbox" class="btn-check" id="btn-light" v-model="visibleTypes.light" autocomplete="off">
                <label class="btn btn-outline-info" for="btn-light">Light Level</label>
              </div>
            </div>

            <div v-if="errorMessage" class="alert alert-danger" role="alert">
              {{ errorMessage }}
            </div>

            <div v-else-if="isLoading" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-3 mb-0">Loading report data...</p>
            </div>

            <div v-else-if="!selectedDeviceId || !hasAnyData" class="text-center py-5 text-muted bg-light rounded">
              <i class="fas fa-chart-area fa-3x mb-3"></i>
              <p>No data found for the selected criteria.</p>
            </div>

            <div v-else class="row">
              <div class="col-md-12">
                <h5 class="text-center mb-3 text-secondary">{{ reportTitle }}</h5>
                <div class="chart-container">
                  <canvas ref="mainCanvas"></canvas>
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

const rangeSelection = ref('daily');
const startDate = ref('');
const endDate = ref('');

const reportData = ref(null);
const mainCanvas = ref(null);
let mainChart = null;

const visibleTypes = ref({
  soil: true,
  temp: true,
  hum: true,
  light: true
});

const reportTitle = computed(() => {
  if (rangeSelection.value === 'daily') return 'Last 24 Hours Trends';
  if (rangeSelection.value === 'weekly') return 'Last 7 Days Trends';
  if (rangeSelection.value === 'monthly') return 'Last 30 Days Trends';
  return `Range: ${startDate.value} to ${endDate.value}`;
});

const hasAnyData = computed(() => {
  return reportData.value && reportData.value.labels && reportData.value.labels.length > 0;
});

const chartConfig = (labels, data) => {
  const datasets = [];
  
  if (visibleTypes.value.soil) {
    datasets.push({
      label: 'Soil Moisture (%)',
      data: data.soil_moisture,
      borderColor: '#0d6efd',
      backgroundColor: 'rgba(13,110,253,0.15)',
      tension: 0.3
    });
  }
  
  if (visibleTypes.value.temp) {
    datasets.push({
      label: 'Temperature (°C)',
      data: data.temperature,
      borderColor: '#fd7e14',
      backgroundColor: 'rgba(253,126,20,0.15)',
      tension: 0.3
    });
  }
  
  if (visibleTypes.value.hum) {
    datasets.push({
      label: 'Humidity (%)',
      data: data.humidity,
      borderColor: '#198754',
      backgroundColor: 'rgba(25,135,84,0.15)',
      tension: 0.3
    });
  }
  
  if (visibleTypes.value.light) {
    datasets.push({
      label: 'Light Level (lx)',
      data: data.light_level,
      borderColor: '#36b9cc',
      backgroundColor: 'rgba(54,185,204,0.15)',
      tension: 0.3
    });
  }

  return {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        y: { beginAtZero: false }
      }
    }
  };
};

const destroyChart = () => {
  if (mainChart) {
    mainChart.destroy();
    mainChart = null;
  }
};

const renderChart = async () => {
  destroyChart();
  await nextTick();
  if (!hasAnyData.value || !mainCanvas.value) return;
  mainChart = new Chart(mainCanvas.value.getContext('2d'), chartConfig(reportData.value.labels, reportData.value));
};

const loadDevices = async () => {
  devicesLoading.value = true;
  try {
    const result = await apiService.getReportDevices();
    devices.value = Array.isArray(result) ? result : [];
    if (devices.value.length > 0) {
      selectedDeviceId.value = devices.value[0].id;
    }
  } catch (error) {
    errorMessage.value = 'Failed to load devices.';
  } finally {
    devicesLoading.value = false;
  }
};

const loadReports = async () => {
  if (!selectedDeviceId.value) return;

  isLoading.value = true;
  errorMessage.value = '';
  try {
    let result;
    if (rangeSelection.value === 'daily') {
      result = await apiService.getReportsDaily(selectedDeviceId.value);
    } else if (rangeSelection.value === 'weekly') {
      result = await apiService.getReportsWeekly(selectedDeviceId.value);
    } else if (rangeSelection.value === 'monthly') {
      result = await apiService.getReportsMonthly(selectedDeviceId.value);
    } else if (rangeSelection.value === 'custom') {
      if (!startDate.value || !endDate.value) {
        throw new Error('Please select both start and end dates.');
      }
      // Add time components for the full range
      const startIso = new Date(startDate.value + 'T00:00:00').toISOString();
      const endIso = new Date(endDate.value + 'T23:59:59').toISOString();
      result = await apiService.getReportsCustom(selectedDeviceId.value, startIso, endIso);
    }
    
    reportData.value = result;
    await renderChart();
  } catch (error) {
    errorMessage.value = error.message || 'Failed to load report data.';
    reportData.value = null;
    destroyChart();
  } finally {
    isLoading.value = false;
  }
};

const handleExport = async () => {
  if (!selectedDeviceId.value) return;
  try {
    let start, end;
    const now = new Date();
    
    if (rangeSelection.value === 'daily') {
      end = now.toISOString();
      start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    } else if (rangeSelection.value === 'weekly') {
      end = now.toISOString();
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
    } else if (rangeSelection.value === 'monthly') {
      end = now.toISOString();
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
    } else {
      if (!startDate.value || !endDate.value) {
        alert('Please select date range first.');
        return;
      }
      start = new Date(startDate.value + 'T00:00:00').toISOString();
      end = new Date(endDate.value + 'T23:59:59').toISOString();
    }
    
    await apiService.exportReportCSV(selectedDeviceId.value, start, end);
  } catch (error) {
    alert('Export failed: ' + error.message);
  }
};

watch([selectedDeviceId, rangeSelection], () => {
  if (rangeSelection.value !== 'custom') {
    loadReports();
  }
});

watch(visibleTypes, () => {
  renderChart();
}, { deep: true });

onMounted(async () => {
  // Set default dates for custom picker (last 7 days)
  const today = new Date();
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  endDate.value = today.toISOString().split('T')[0];
  startDate.value = weekAgo.toISOString().split('T')[0];
  
  await loadDevices();
  if (selectedDeviceId.value) {
    await loadReports();
  }
});

onBeforeUnmount(() => {
  destroyChart();
});
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 450px;
}
.border-left-primary { border-left: 0.25rem solid #4e73df !important; }
</style>
