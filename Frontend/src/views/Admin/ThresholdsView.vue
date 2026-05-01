<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-10">
        <div class="card shadow">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h4 class="mb-0">Alert Thresholds Management</h4>
            <button class="btn btn-sm btn-outline-light" @click="resetToDefaults" :disabled="loading || saving">
              <i class="fas fa-undo"></i> Reset to Defaults
            </button>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-2">Loading settings...</p>
            </div>
            
            <form v-else-if="thresholds" @submit.prevent="saveThresholds">
              <p class="text-muted mb-4">Set system-wide thresholds for triggering alerts and managing device behavior.</p>
              
              <div class="row">
                <!-- Temperature -->
                <div class="col-md-6">
                  <div class="card mb-4 border-left-warning">
                    <div class="card-body">
                      <h5 class="card-title text-warning"><i class="fas fa-thermometer-half"></i> Temperature (°C)</h5>
                      <div class="mb-3">
                        <label for="tempHigh" class="form-label">High Temperature Warning</label>
                        <input type="number" step="0.1" id="tempHigh" class="form-control" v-model.number="thresholds.temperature_high" required>
                      </div>
                      <div class="mb-3">
                        <label for="tempCritical" class="form-label">Critical Temperature Warning</label>
                        <input type="number" step="0.1" id="tempCritical" class="form-control" v-model.number="thresholds.temperature_critical" required>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Humidity -->
                <div class="col-md-6">
                  <div class="card mb-4 border-left-info">
                    <div class="card-body">
                      <h5 class="card-title text-info"><i class="fas fa-tint"></i> Humidity (%)</h5>
                      <div class="mb-3">
                        <label for="humidityLow" class="form-label">Low Humidity Warning</label>
                        <input type="number" step="0.1" min="0" max="100" id="humidityLow" class="form-control" v-model.number="thresholds.humidity_low" required>
                      </div>
                      <div class="mb-3">
                        <label for="humidityHigh" class="form-label">High Humidity Warning</label>
                        <input type="number" step="0.1" min="0" max="100" id="humidityHigh" class="form-control" v-model.number="thresholds.humidity_high" required>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Soil Moisture -->
                <div class="col-md-6">
                  <div class="card mb-4 border-left-primary">
                    <div class="card-body">
                      <h5 class="card-title text-primary"><i class="fas fa-seedling"></i> Soil Moisture (%)</h5>
                      <div class="mb-3">
                        <label for="moistureLow" class="form-label">Low Moisture Warning</label>
                        <input type="number" step="0.1" min="0" max="100" id="moistureLow" class="form-control" v-model.number="thresholds.soil_moisture_low" required>
                      </div>
                      <div class="mb-3">
                        <label for="moistureCritical" class="form-label">Critical Moisture Warning</label>
                        <input type="number" step="0.1" min="0" max="100" id="moistureCritical" class="form-control" v-model.number="thresholds.soil_moisture_critical" required>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- System Configuration -->
                <div class="col-md-6">
                  <div class="card mb-4 border-left-success">
                    <div class="card-body">
                      <h5 class="card-title text-success"><i class="fas fa-cog"></i> System Configuration</h5>
                      <div class="mb-3">
                        <label for="updateFrequency" class="form-label">Data Update Frequency</label>
                        <select id="updateFrequency" class="form-select" v-model.number="thresholds.update_frequency" required>
                          <option value="1">1 Minute</option>
                          <option value="5">5 Minutes</option>
                          <option value="10">10 Minutes</option>
                          <option value="15">15 Minutes</option>
                          <option value="30">30 Minutes</option>
                          <option value="60">60 Minutes</option>
                        </select>
                      </div>
                      <div class="mb-3">
                        <label for="notes" class="form-label">Configuration Notes</label>
                        <textarea id="notes" class="form-control" rows="2" v-model="thresholds.notes" placeholder="Optional notes about this configuration..."></textarea>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="d-grid gap-2 d-md-flex justify-content-md-end mt-3">
                <button type="submit" class="btn btn-primary btn-lg" :disabled="saving">
                  <span v-if="saving" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  <i v-else class="fas fa-save"></i> {{ saving ? 'Saving...' : 'Save All Settings' }}
                </button>
              </div>
            </form>
            
            <div v-if="errorMessage" class="alert alert-danger mt-3 alert-dismissible fade show" role="alert">
              <i class="fas fa-exclamation-triangle"></i> {{ errorMessage }}
              <button type="button" class="btn-close" @click="errorMessage = ''"></button>
            </div>
            <div v-if="successMessage" class="alert alert-success mt-3 alert-dismissible fade show" role="alert">
              <i class="fas fa-check-circle"></i> {{ successMessage }}
              <button type="button" class="btn-close" @click="successMessage = ''"></button>
            </div>
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
  await loadThresholds();
});

const loadThresholds = async () => {
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
};

const saveThresholds = async () => {
  if (!thresholds.value) return;
  
  // Extra validation for 0-100 fields
  const percentageFields = ['humidity_low', 'humidity_high', 'soil_moisture_low', 'soil_moisture_critical'];
  for (const field of percentageFields) {
    if (thresholds.value[field] < 0 || thresholds.value[field] > 100) {
      errorMessage.value = `Field ${field.replace('_', ' ')} must be between 0 and 100.`;
      return;
    }
  }

  try {
    saving.value = true;
    successMessage.value = '';
    errorMessage.value = '';
    await apiService.updateAlertThresholds(thresholds.value);
    successMessage.value = 'Settings saved successfully!';
    setTimeout(() => { successMessage.value = ''; }, 5000);
  } catch (error) {
    console.error('Failed to save thresholds:', error);
    errorMessage.value = 'Failed to save settings: ' + (error.message || 'Unknown error');
  } finally {
    saving.value = false;
  }
};

const resetToDefaults = async () => {
  if (!confirm('Are you sure you want to reset all thresholds to system defaults? This will not be saved until you click "Save All Settings".')) {
    return;
  }
  
  try {
    loading.value = true;
    const defaults = await apiService.getDefaultAlertThresholds();
    thresholds.value = defaults;
    successMessage.value = 'Thresholds reset to defaults (unsaved).';
    setTimeout(() => { successMessage.value = ''; }, 3000);
  } catch (error) {
    console.error('Failed to load default thresholds:', error);
    errorMessage.value = 'Failed to load default settings.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.border-left-primary { border-left: 4px solid #4e73df !important; }
.border-left-success { border-left: 4px solid #1cc88a !important; }
.border-left-info { border-left: 4px solid #36b9cc !important; }
.border-left-warning { border-left: 4px solid #f6c23e !important; }
.border-left-danger { border-left: 4px solid #e74a3b !important; }

.card-title {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 0.05rem;
  margin-bottom: 1.25rem;
}

.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}
</style>
