<template>
  <div class="row">
    <!-- Temperature Sensor Card -->
    <div class="col-xl-4 col-md-6 mb-4">
      <div class="card h-100" :class="temperatureCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Temperature</div>
              <div id="temperatureValue" class="h5 mb-0 font-weight-bold">{{ formattedTemperature }}</div>
              <div id="temperatureTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
            </div>
            <div class="col-auto">
              <i class="fas fa-thermometer-half fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Humidity Sensor Card -->
    <div class="col-xl-4 col-md-6 mb-4">
      <div class="card h-100" :class="humidityCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Humidity</div>
              <div id="humidityValue" class="h5 mb-0 font-weight-bold">{{ formattedHumidity }}</div>
              <div id="humidityTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
            </div>
            <div class="col-auto">
              <i class="fas fa-tint fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Soil Moisture Sensor Card -->
    <div class="col-xl-4 col-md-6 mb-4">
      <div class="card h-100" :class="moistureCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Soil Moisture</div>
              <div id="moistureValue" class="h5 mb-0 font-weight-bold">{{ formattedMoisture }}</div>
              <div id="moistureTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
            </div>
            <div class="col-auto">
              <i class="fas fa-seedling fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineExpose } from 'vue';
import { firebaseService } from '@/services/firebase';
import { apiService } from '@/services/api';
import { formatNumber } from '@/utils/helpers';
import { SENSOR_THRESHOLDS } from '@/config';

const deviceId = ref(localStorage.getItem('selectedDeviceId') || 'device_001');
const temperature = ref(null);
const humidity = ref(null);
const moisture = ref(null);
const lastUpdateTime = ref('N/A');

// Format values for display
const formattedTemperature = computed(() => temperature.value !== null ? `${formatNumber(temperature.value)}°C` : 'N/A');
const formattedHumidity = computed(() => humidity.value !== null ? `${formatNumber(humidity.value)}%` : 'N/A');
const formattedMoisture = computed(() => moisture.value !== null ? `${formatNumber(moisture.value)}%` : 'N/A');

// Update data from listener or fetch
const updateDisplay = (data) => {
  if (!data) return;

  if (data.temperature !== undefined) temperature.value = data.temperature;
  if (data.humidity !== undefined) humidity.value = data.humidity;
  if (data.moisture !== undefined) moisture.value = data.moisture;

  if (data.timestamp) {
    lastUpdateTime.value = `Last updated: ${new Date(data.timestamp * 1000).toLocaleTimeString()}`;
  }
};

onMounted(async () => {
  // Fetch initial data
  const initialData = await apiService.getLatestSensorData(deviceId.value);
  updateDisplay(initialData);

  // Subscribe to real-time updates
  await firebaseService.initialize();
  firebaseService.subscribeToSensorData(deviceId.value, (data) => {
    updateDisplay(data);
  });
});

// Dynamic card classes for visual feedback
const temperatureCardClass = computed(() => {
  if (temperature.value > SENSOR_THRESHOLDS.TEMP_HIGH_WARNING) return 'bg-danger text-white';
  return 'bg-primary text-white';
});

const humidityCardClass = computed(() => {
  if (humidity.value > 80 || humidity.value < 20) return 'bg-warning text-dark';
  return 'bg-info text-white';
});

const moistureCardClass = computed(() => {
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_CRITICAL) return 'bg-danger text-white';
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_WARNING) return 'bg-warning text-dark';
  return 'bg-success text-white';
});

// Expose method for parent components to check critical conditions
const checkCriticalConditions = () => {
  const criticalAlerts = [];
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_CRITICAL) {
    criticalAlerts.push({
      type: 'moisture_critical',
      message: `CRITICAL: Soil moisture at ${formattedMoisture.value} is extremely low!`,
      priority: 1
    });
  }
  if (temperature.value > SENSOR_THRESHOLDS.TEMP_HIGH_WARNING) {
    criticalAlerts.push({
      type: 'high_temperature',
      message: `WARNING: High temperature detected (${formattedTemperature.value})`,
      priority: 2
    });
  }
  return criticalAlerts;
};

defineExpose({
  checkCriticalConditions,
});
</script>

<style scoped>
.card .fa-2x {
  color: rgba(255, 255, 255, 0.5);
}
.text-dark .fa-2x {
  color: rgba(0, 0, 0, 0.3);
}
.card {
  transition: all 0.3s ease-in-out;
}
</style>
