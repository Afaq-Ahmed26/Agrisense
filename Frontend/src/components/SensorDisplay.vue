<template>
  <div class="row">
    <!-- Temperature Sensor Card -->
    <div class="col-xl-3 col-md-6 mb-4">
      <div class="card h-100" :class="temperatureCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Temperature</div>
              <div v-if="temperature !== null">
                <div id="temperatureValue" class="h5 mb-0 font-weight-bold">{{ formattedTemperature }}</div>
              </div>
              <div v-else class="text-warning small font-weight-bold">
                <i class="fas fa-exclamation-triangle"></i> Sensor Offline
              </div>
              <div id="temperatureTime" class="text-xs mb-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="(deviceStatus?.online ?? true) ? 'text-success' : 'text-danger'">●</span>
                {{ (deviceStatus?.online ?? true) ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus?.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
              </div>
            </div>
            <div class="col-auto">
              <i class="fas fa-thermometer-half fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Humidity Sensor Card -->
    <div class="col-xl-3 col-md-6 mb-4">
      <div class="card h-100" :class="humidityCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Humidity</div>
              <div v-if="humidity !== null">
                <div id="humidityValue" class="h5 mb-0 font-weight-bold">{{ formattedHumidity }}</div>
              </div>
              <div v-else class="text-warning small font-weight-bold">
                <i class="fas fa-exclamation-triangle"></i> Sensor Offline
              </div>
              <div id="humidityTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="(deviceStatus?.online ?? true) ? 'text-success' : 'text-danger'">●</span>
                {{ (deviceStatus?.online ?? true) ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus?.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
              </div>
            </div>
            <div class="col-auto">
              <i class="fas fa-tint fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Soil Moisture Sensor Card -->
    <div class="col-xl-3 col-md-6 mb-4">
      <div class="card h-100" :class="moistureCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Soil Moisture</div>
              <div v-if="moisture !== null">
                <div id="moistureValue" class="h5 mb-0 font-weight-bold">{{ formattedMoisture }}</div>
              </div>
              <div v-else class="text-warning small font-weight-bold">
                <i class="fas fa-exclamation-triangle"></i> Sensor Offline
              </div>
              <div id="moistureTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="(deviceStatus?.online ?? true) ? 'text-success' : 'text-danger'">●</span>
                {{ (deviceStatus?.online ?? true) ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus?.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
              </div>
            </div>
            <div class="col-auto">
              <i class="fas fa-seedling fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Light Level Sensor Card -->
    <div class="col-xl-3 col-md-6 mb-4">
      <div class="card h-100" :class="lightLevelCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Light Level</div>
              <div v-if="lightLevel !== null">
                <div id="lightLevelValue" class="h5 mb-0 font-weight-bold">{{ formattedLightLevel }}</div>
              </div>
              <div v-else class="text-warning small font-weight-bold">
                <i class="fas fa-exclamation-triangle"></i> Sensor Offline
              </div>
              <div id="lightLevelTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="(deviceStatus?.online ?? true) ? 'text-success' : 'text-danger'">●</span>
                {{ (deviceStatus?.online ?? true) ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus?.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
              </div>
            </div>
            <div class="col-auto">
              <i class="fas fa-sun fa-2x"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, inject } from 'vue';
import { formatNumber } from '@/utils/helpers';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { SENSOR_THRESHOLDS } from '@/config';
import { authStore } from '@/store/auth';

const props = defineProps({
  sensorData: {
    type: Object,
    default: () => ({
      temperature: null,
      humidity: null,
      soil_moisture: null,
      light_level: null,
      last_updated: null
    })
  },
  deviceStatus: {
    type: Object,
    default: () => ({
      online: false,
      last_heartbeat: null,
      battery_level: null
    })
  }
});

const temperature = computed(() => props.sensorData?.temperature ?? null);
const humidity = computed(() => props.sensorData?.humidity ?? null);
const moisture = computed(() => props.sensorData?.soil_moisture ?? null);
const lightLevel = computed(() => props.sensorData?.light_level ?? null);
const lastUpdateTime = computed(() => props.sensorData?.last_updated 
  ? `Last updated: ${new Date(props.sensorData.last_updated).toLocaleTimeString()}` 
  : 'Last updated: Never');


const formattedTemperature = computed(() => {
  if (temperature.value === null) return 'N/A';
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  const result = formatWithUserPreferences(temperature.value, 'temperature', userPrefs);
  return `${formatNumber(result.value)}${result.unit}`;
});

const formattedHumidity = computed(() => humidity.value !== null ? `${formatNumber(humidity.value)}%` : 'N/A');
const formattedMoisture = computed(() => moisture.value !== null ? `${formatNumber(moisture.value)}%` : 'N/A');
const formattedLightLevel = computed(() => lightLevel.value !== null ? `${formatNumber(lightLevel.value)} lx` : 'N/A');

const temperatureCardClass = computed(() => {
  if (temperature.value === null) return 'bg-secondary text-white';
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  const tempThreshold = formatWithUserPreferences(SENSOR_THRESHOLDS.TEMP_HIGH_WARNING, 'temperature', userPrefs);
  if (temperature.value > tempThreshold.value) return 'bg-danger text-white';
  return 'bg-primary text-white';
});

const humidityCardClass = computed(() => {
  if (humidity.value === null) return 'bg-secondary text-white';
  if (humidity.value > 80 || humidity.value < 20) return 'bg-warning text-dark';
  return 'bg-info text-white';
});

const moistureCardClass = computed(() => {
  if (moisture.value === null) return 'bg-secondary text-white';
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_CRITICAL) return 'bg-danger text-white';
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_WARNING) return 'bg-warning text-dark';
  return 'bg-success text-white';
});

const lightLevelCardClass = computed(() => {
  if (lightLevel.value === null) return 'bg-secondary text-white';
  if (lightLevel.value > 1000) return 'bg-light text-dark';
  return 'bg-secondary text-white';
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
