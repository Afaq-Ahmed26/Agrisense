<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-10">
        <div class="card">
          <div class="card-header">
            <h4>Alert Thresholds Management</h4>
            <p>Set system-wide thresholds for triggering alerts.</p>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center">
              <p>Loading settings...</p>
            </div>
            <form v-else-if="thresholds" @submit.prevent="saveThresholds">
              <!-- Temperature -->
              <h5 class="mt-4">Temperature (°C)</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="tempHigh" class="form-label">High Temperature Warning</label>
                  <input type="number" step="0.1" id="tempHigh" class="form-control" v-model.number="thresholds.temperature_high">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="tempCritical" class="form-label">Critical Temperature Warning</label>
                  <input type="number" step="0.1" id="tempCritical" class="form-control" v-model.number="thresholds.temperature_critical">
                </div>
              </div>

              <!-- Humidity -->
              <h5 class="mt-4">Humidity (%)</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="humidityLow" class="form-label">Low Humidity Warning</label>
                  <input type="number" step="0.1" id="humidityLow" class="form-control" v-model.number="thresholds.humidity_low">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="humidityHigh" class="form-label">High Humidity Warning</label>
                  <input type="number" step="0.1" id="humidityHigh" class="form-control" v-model.number="thresholds.humidity_high">
                </div>
              </div>

              <!-- Soil Moisture -->
              <h5 class="mt-4">Soil Moisture (%)</h5>
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="moistureLow" class="form-label">Low Moisture Warning</label>
                  <input type="number" step="0.1" id="moistureLow" class="form-control" v-model.number="thresholds.soil_moisture_low">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="moistureCritical" class="form-label">Critical Moisture Warning</label>
                  <input type="number" step="0.1" id="moistureCritical" class="form-control" v-model.number="thresholds.soil_moisture_critical">
                </div>
              </div>

              <hr>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Saving...' : 'Save All Settings' }}
              </button>
            </form>
            <div v-if="errorMessage" class="alert alert-danger mt-3">{{ errorMessage }}</div>
            <div v-if="successMessage" class="alert alert-success mt-3">{{ successMessage }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiService } from '@/services/api';

const thresholds = ref(null);
const loading = ref(true);
const saving = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

onMounted(async () => {
  try {
    loading.value = true;
    thresholds.value = await apiService.getAlertThresholds();
    errorMessage.value = '';
  } catch (error) {
    console.error('Failed to load alert thresholds:', error);
    errorMessage.value = 'Failed to load settings. You may not have permission to view this page.';
  } finally {
    loading.value = false;
  }
});

const saveThresholds = async () => {
  if (!thresholds.value) return;
  try {
    saving.value = true;
    successMessage.value = '';
    errorMessage.value = '';
    await apiService.updateAlertThresholds(thresholds.value);
    successMessage.value = 'Settings saved successfully!';
  } catch (error) {
    console.error('Failed to save thresholds:', error);
    errorMessage.value = 'Failed to save settings.';
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for ThresholdsView */
.card-header h4 {
  margin-bottom: 0.25rem;
}
</style>
