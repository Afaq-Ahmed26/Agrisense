<template>
  <div class="container">
    <div class="row justify-content-center align-items-center min-vh-100">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-3">
          <div class="card-header text-center bg-info text-white py-4 rounded-top-3">
            <h2 class="mb-0"><i class="fas fa-envelope-open-text me-2"></i>Check Your Email</h2>
          </div>
          <div class="card-body p-4">
            <p class="mb-3">
              A verification link has been sent to <strong>{{ userEmail }}</strong>.
            </p>
            <p class="text-muted mb-4">We are checking your verification status automatically.</p>

            <div class="d-grid gap-2">
              <button
                class="btn btn-primary"
                @click="resendVerification"
                :disabled="isResending || resendCooldown > 0"
              >
                <span v-if="isResending" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                <span v-if="resendCooldown > 0">Resend in {{ resendCooldown }}s</span>
                <span v-else>Resend Verification Link</span>
              </button>
              <button class="btn btn-outline-secondary" @click="goBackToRegister">
                Wrong email? Go back
              </button>
            </div>

            <div v-if="errorMessage" class="alert alert-danger mt-3 mb-0" role="alert">
              {{ errorMessage }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authService } from '@/services/auth';
import { authStore } from '@/store/auth';
import { firebaseService } from '@/services/firebase';

const route = useRoute();
const router = useRouter();

const isResending = ref(false);
const resendCooldown = ref(0);
const errorMessage = ref('');

let pollIntervalId = null;
let cooldownIntervalId = null;

const userEmail = computed(() => authStore.user?.email || route.query.email || 'your account email');

const startCooldown = (seconds = 30) => {
  resendCooldown.value = seconds;
  if (cooldownIntervalId) {
    clearInterval(cooldownIntervalId);
  }
  cooldownIntervalId = setInterval(() => {
    if (resendCooldown.value <= 0) {
      clearInterval(cooldownIntervalId);
      cooldownIntervalId = null;
      return;
    }
    resendCooldown.value -= 1;
  }, 1000);
};

const checkVerificationStatus = async () => {
  try {
    const result = await authService.checkEmailVerificationStatus();
    if (result.success && result.verified) {
      router.replace('/dashboard');
    }
  } catch (error) {
    // keep waiting silently unless it is a hard auth problem
  }
};

const resendVerification = async () => {
  errorMessage.value = '';
  isResending.value = true;
  try {
    const result = await authService.sendVerificationEmail();
    if (!result.success) {
      errorMessage.value = result.message;
      return;
    }
    startCooldown(30);
  } catch (error) {
    errorMessage.value = error.message || 'Failed to resend verification email.';
  } finally {
    isResending.value = false;
  }
};

const goBackToRegister = async () => {
  await authService.logout();
  router.replace('/register');
};

onMounted(async () => {
  if (!authStore.token || !firebaseService.auth?.currentUser) {
    router.replace('/login');
    return;
  }
  await checkVerificationStatus();
  pollIntervalId = setInterval(checkVerificationStatus, 4000);
});

onBeforeUnmount(() => {
  if (pollIntervalId) clearInterval(pollIntervalId);
  if (cooldownIntervalId) clearInterval(cooldownIntervalId);
});
</script>
