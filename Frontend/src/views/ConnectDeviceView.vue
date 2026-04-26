<template>
  <div class="connect-device-view">
    <h2>Connect Device</h2>

    <div v-if="isAdmin" class="card mb-4">
      <div class="card-body">
        <h5 class="card-title">Admin: Generate Pairing Code</h5>
        <form @submit.prevent="handleGeneratePairingCode">
          <div class="mb-3">
            <label for="adminDeviceId" class="form-label">Device ID</label>
            <input
              id="adminDeviceId"
              v-model="pairingForm.deviceId"
              type="text"
              class="form-control"
              placeholder="esp32-b47cb8"
              required
            />
          </div>
          <div class="mb-3">
            <label for="expiresMinutes" class="form-label">Code Expiry (minutes)</label>
            <input
              id="expiresMinutes"
              v-model.number="pairingForm.expiresMinutes"
              type="number"
              min="1"
              max="60"
              class="form-control"
              required
            />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isGeneratingCode">
            <span v-if="isGeneratingCode" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span v-else>Generate Pairing Code</span>
          </button>
        </form>

        <div v-if="generatedCode" class="alert alert-success mt-3 mb-0">
          <div><strong>Pairing Code:</strong> {{ generatedCode.pairing_code }}</div>
          <div><strong>Expires At:</strong> {{ generatedCode.expires_at }}</div>
        </div>
      </div>
    </div>

    <div v-if="isFarmer" class="card mb-4">
      <div class="card-body">
        <h5 class="card-title">Farmer: Claim Device</h5>
        <form @submit.prevent="handleClaimDevice">
          <div class="mb-3">
            <label for="claimDeviceId" class="form-label">Device ID</label>
            <input
              id="claimDeviceId"
              v-model="claimForm.deviceId"
              type="text"
              class="form-control"
              placeholder="esp32-b47cb8"
              required
            />
          </div>
          <div class="mb-3">
            <label for="pairingCode" class="form-label">Pairing Code</label>
            <input
              id="pairingCode"
              v-model="claimForm.pairingCode"
              type="text"
              class="form-control"
              placeholder="6-digit code"
              required
            />
          </div>
          <button type="submit" class="btn btn-success" :disabled="isClaimingDevice">
            <span v-if="isClaimingDevice" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span v-else>Claim Device</span>
          </button>
        </form>
      </div>
    </div>

    <div v-if="message" class="alert alert-success">{{ message }}</div>
    <div v-if="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>
    <div v-if="!isAdmin && !isFarmer" class="alert alert-info mb-0">
      Device self-claim is disabled for your role. Ask an admin or assigned farmer to manage device ownership.
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { apiService } from '@/services/api';
import { authStore, fetchUser } from '@/store/auth';

const pairingForm = ref({
  deviceId: '',
  expiresMinutes: 10
});
const claimForm = ref({
  deviceId: '',
  pairingCode: ''
});

const isGeneratingCode = ref(false);
const isClaimingDevice = ref(false);
const generatedCode = ref(null);
const message = ref('');
const errorMessage = ref('');

const normalizedRole = computed(() => (authStore.user?.role || '').toLowerCase());
const isAdmin = computed(() => normalizedRole.value === 'admin');
const isFarmer = computed(() => normalizedRole.value === 'farmer');

const clearMessages = () => {
  message.value = '';
  errorMessage.value = '';
};

const handleGeneratePairingCode = async () => {
  clearMessages();
  generatedCode.value = null;
  isGeneratingCode.value = true;

  try {
    const response = await apiService.generateDevicePairingCode(
      pairingForm.value.deviceId.trim(),
      pairingForm.value.expiresMinutes
    );
    generatedCode.value = response;
    message.value = `Pairing code generated for ${response.device_id}.`;
  } catch (error) {
    errorMessage.value = error.message || 'Failed to generate pairing code.';
  } finally {
    isGeneratingCode.value = false;
  }
};

const handleClaimDevice = async () => {
  clearMessages();
  isClaimingDevice.value = true;

  try {
    const response = await apiService.claimDevice(
      claimForm.value.deviceId.trim(),
      claimForm.value.pairingCode.trim()
    );
    await fetchUser();
    message.value = response.message || 'Device claimed successfully.';
  } catch (error) {
    errorMessage.value = error.message || 'Failed to claim device.';
  } finally {
    isClaimingDevice.value = false;
  }
};
</script>

<style scoped>
.connect-device-view {
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
