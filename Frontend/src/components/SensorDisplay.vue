<template>
  <div class="row">
    <!-- Temperature Sensor Card -->
    <div class="col-xl-3 col-md-6 mb-4">
      <div class="card h-100" :class="temperatureCardClass">
        <div class="card-body">
          <div class="row no-gutters align-items-center">
            <div class="col mr-2">
              <div class="text-xs font-weight-bold text-uppercase mb-1">Temperature</div>
              <div id="temperatureValue" class="h5 mb-0 font-weight-bold">{{ formattedTemperature }}</div>
              <div id="temperatureTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="deviceStatus.online ? 'text-success' : 'text-danger'">●</span>
                {{ deviceStatus.online ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
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
              <div id="humidityValue" class="h5 mb-0 font-weight-bold">{{ formattedHumidity }}</div>
              <div id="humidityTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="deviceStatus.online ? 'text-success' : 'text-danger'">●</span>
                {{ deviceStatus.online ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
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
              <div id="moistureValue" class="h5 mb-0 font-weight-bold">{{ formattedMoisture }}</div>
              <div id="moistureTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="deviceStatus.online ? 'text-success' : 'text-danger'">●</span>
                {{ deviceStatus.online ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
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
              <div id="lightLevelValue" class="h5 mb-0 font-weight-bold">{{ formattedLightLevel }}</div>
              <div id="lightLevelTime" class="text-xs mt-1">{{ lastUpdateTime }}</div>
              <div class="text-xs mt-1">
                <span :class="deviceStatus.online ? 'text-success' : 'text-danger'">●</span>
                {{ deviceStatus.online ? 'Online' : 'Offline' }}
                <span v-if="deviceStatus.last_heartbeat">- Last heartbeat: {{ new Date(deviceStatus.last_heartbeat).toLocaleTimeString() }}</span>
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
      temperature: 25,
      humidity: 60,
      soil_moisture: 45,
      light_level: 800,
      last_updated: new Date().toISOString()
    })
  },
  deviceStatus: {
    type: Object,
    default: () => ({
      online: true,
      last_heartbeat: new Date().toISOString(),
      battery_level: 95
    })
  }
});

const temperature = computed(() => props.sensorData.temperature);
const humidity = computed(() => props.sensorData.humidity);
const moisture = computed(() => props.sensorData.soil_moisture);
const lightLevel = computed(() => props.sensorData.light_level);
const lastUpdateTime = computed(() => `Last updated: ${new Date(props.sensorData.last_updated).toLocaleTimeString()}`);


const formattedTemperature = computed(() => {
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  const result = formatWithUserPreferences(temperature.value, 'temperature', userPrefs);
  return `${formatNumber(result.value)}${result.unit}`;
});

const formattedHumidity = computed(() => `${formatNumber(humidity.value)}%`);
const formattedMoisture = computed(() => `${formatNumber(moisture.value)}%`);
const formattedLightLevel = computed(() => `${formatNumber(lightLevel.value)} lx`);

const temperatureCardClass = computed(() => {
  // For temperature threshold comparison, we need to convert the threshold to the current unit
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
  if (humidity.value > 80 || humidity.value < 20) return 'bg-warning text-dark';
  return 'bg-info text-white';
});

const moistureCardClass = computed(() => {
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_CRITICAL) return 'bg-danger text-white';
  if (moisture.value < SENSOR_THRESHOLDS.MOISTURE_WARNING) return 'bg-warning text-dark';
  return 'bg-success text-white';
});

const lightLevelCardClass = computed(() => {
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
