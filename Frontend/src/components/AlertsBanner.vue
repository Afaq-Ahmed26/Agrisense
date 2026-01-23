<template>
  <div v-if="activeAlerts.length > 0" class="alerts-container">
    <div
      v-for="alert in sortedAlerts"
      :key="alert.id"
      class="alert alert-dismissible fade show"
      :class="alertClass(alert.type)"
      role="alert"
    >
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>
            <i :class="alertIcon(alert.type)" class="me-2"></i>
            {{ formatAlertType(alert.type) }}
          </strong>
          <div>{{ alert.message }}</div>
          <small class="opacity-75">{{ formatAlertTime(alert.created_at) }}</small>
        </div>
        <button
          type="button"
          class="btn-close"
          @click="acknowledge(alert.id)"
          aria-label="Close"
        ></button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiService } from '@/services/api';
import { firebaseService } from '@/services/firebase';
import { MAX_ALERTS_DISPLAYED, ALERTS_REFRESH_INTERVAL } from '@/config';

const deviceId = ref(localStorage.getItem('selectedDeviceId') || 'device_001');
const activeAlerts = ref([]);

onMounted(async () => {
  await fetchAlerts();
  
  await firebaseService.initialize();
  firebaseService.subscribeToAlerts(deviceId.value, (alerts) => {
    activeAlerts.value = alerts;
  });

  setInterval(fetchAlerts, ALERTS_REFRESH_INTERVAL);
});

const fetchAlerts = async () => {
  try {
    const response = await apiService.getActiveAlerts(deviceId.value);
    activeAlerts.value = response.alerts || [];
  } catch (error) {
    console.error('Failed to fetch active alerts:', error);
  }
};

const sortedAlerts = computed(() => {
  return [...activeAlerts.value]
    .sort((a, b) => getAlertPriority(a.type) - getAlertPriority(b.type) || new Date(b.created_at) - new Date(a.created_at))
    .slice(0, MAX_ALERTS_DISPLAYED);
});

const acknowledge = async (alertId) => {
  try {
    await apiService.acknowledgeAlert(alertId);
    activeAlerts.value = activeAlerts.value.filter(a => a.id !== alertId);
  } catch (error) {
    console.error(`Failed to acknowledge alert ${alertId}:`, error);
  }
};

const getAlertPriority = (type) => {
  const priorities = { 'critical': 1, 'warning': 2, 'info': 3 };
  const key = Object.keys(priorities).find(p => type.includes(p));
  return key ? priorities[key] : 3;
};

const alertClass = (type) => {
  const priority = getAlertPriority(type);
  if (priority === 1) return 'alert-danger';
  if (priority === 2) return 'alert-warning';
  return 'alert-info';
};

const alertIcon = (type) => {
  const priority = getAlertPriority(type);
  if (priority === 1) return 'fas fa-exclamation-triangle';
  if (priority === 2) return 'fas fa-exclamation-circle';
  return 'fas fa-info-circle';
};

const formatAlertType = (type) => type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

const formatAlertTime = (timestamp) => {
  if (!timestamp) return 'Just now';
  const diffMinutes = Math.floor((new Date() - new Date(timestamp)) / 60000);
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
  return `${Math.floor(diffMinutes / 1440)}d ago`;
};
</script>

<style scoped>
.alerts-container {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 350px;
  z-index: 1050;
}
.alert {
  margin-bottom: 1rem;
}
</style>
