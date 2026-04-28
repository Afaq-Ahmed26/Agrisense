<template>
  <div class="connect-device-view">
    <h2>Connect Device</h2>

    <div v-if="isFarmer" class="card">
      <div class="card-body">
        <h5 class="card-title">Connect by Email OTP</h5>
        <p class="text-muted">OTP will be sent to <strong>{{ userEmail }}</strong></p>

        <form @submit.prevent="handleRequestOtp" class="mb-3">
          <label for="deviceId" class="form-label">Device ID</label>
          <div class="input-group">
            <input
              id="deviceId"
              v-model="deviceId"
              type="text"
              class="form-control"
              placeholder="esp32-b47cb8"
              required
            />
            <button type="submit" class="btn btn-primary" :disabled="isRequestingOtp || !deviceId.trim()">
              <span v-if="isRequestingOtp" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <span v-else>Send OTP</span>
            </button>
          </div>
        </form>

        <form v-if="otpRequested" @submit.prevent="handleVerifyOtp">
          <label for="otpInput" class="form-label">Enter OTP</label>
          <div class="input-group">
            <input
              id="otpInput"
              v-model="otp"
              type="text"
              class="form-control"
              placeholder="6-digit OTP"
              required
            />
            <button type="submit" class="btn btn-success" :disabled="isVerifyingOtp || !otp.trim()">
              <span v-if="isVerifyingOtp" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              <span v-else>Verify & Connect</span>
            </button>
          </div>
          <small class="text-muted d-block mt-2">
            OTP expires in 10 minutes and is blocked after 3 wrong attempts.
          </small>
        </form>
      </div>
    </div>

    <div v-if="message" class="alert alert-success mt-3">{{ message }}</div>
    <div v-if="errorMessage" class="alert alert-danger mt-3">{{ errorMessage }}</div>

    <div v-if="!isFarmer" class="alert alert-info mt-3">
      Device self-connect is available for farmer accounts only.
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { apiService } from '@/services/api';
import { authStore, fetchUser } from '@/store/auth';

const router = useRouter();
const deviceId = ref('');
const otp = ref('');
const otpRequested = ref(false);
const isRequestingOtp = ref(false);
const isVerifyingOtp = ref(false);
const message = ref('');
const errorMessage = ref('');

const role = computed(() => (authStore.user?.role || '').toLowerCase());
const isFarmer = computed(() => role.value === 'farmer');
const userEmail = computed(() => authStore.user?.email || 'your email');

const clearStatus = () => {
  message.value = '';
  errorMessage.value = '';
};

const handleRequestOtp = async () => {
  clearStatus();
  isRequestingOtp.value = true;
  try {
    const response = await apiService.requestDeviceConnectOtp(deviceId.value.trim());
    otpRequested.value = true;
    message.value = response.message || `OTP sent to ${response.email}`;
  } catch (error) {
    otpRequested.value = false;
    errorMessage.value = error.message || 'Failed to send OTP.';
  } finally {
    isRequestingOtp.value = false;
  }
};

const handleVerifyOtp = async () => {
  clearStatus();
  isVerifyingOtp.value = true;
  try {
    const response = await apiService.verifyDeviceConnectOtp(deviceId.value.trim(), otp.value.trim());
    message.value = response.message || 'Device connected successfully.';
    await fetchUser();
    setTimeout(() => router.push('/dashboard'), 800);
  } catch (error) {
    errorMessage.value = error.message || 'Failed to verify OTP.';
  } finally {
    isVerifyingOtp.value = false;
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
