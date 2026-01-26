<template>
  <div class="container">
    <div class="row justify-content-center align-items-center min-vh-100">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-3">
          <div class="card-header text-center bg-primary text-white py-4 rounded-top-3">
            <h2 class="mb-0"><i class="fas fa-seedling me-2"></i>AgriSense</h2>
            <small class="opacity-75">Password Reset</small>
          </div>
          <div class="card-body p-4">
            <p class="text-center text-muted mb-4">Enter your email address to receive a password reset link.</p>
            <form @submit.prevent="handlePasswordReset">
              <div class="mb-3">
                <label for="email" class="form-label">Email Address</label>
                <input type="email" class="form-control" id="email" v-model="email" placeholder="Enter your email" required>
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  Send Reset Link
                </button>
              </div>
            </form>
            
            <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
              {{ successMessage }}
            </div>
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
              {{ errorMessage }}
            </div>

            <div class="text-center mt-3">
              <router-link to="/login" class="text-decoration-none">Back to Login</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { firebaseService } from '@/services/firebase';
import { sendPasswordResetEmail } from 'firebase/auth';

const email = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);
const router = useRouter();

const handlePasswordReset = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    if (!firebaseService.auth) {
      throw new Error("Firebase Auth is not initialized.");
    }
    await sendPasswordResetEmail(firebaseService.auth, email.value);
    successMessage.value = 'If an account with that email exists, a password reset link has been sent to your email address.';
    email.value = ''; // Clear email field
  } catch (error) {
    console.error('Password reset error:', error);
    errorMessage.value = error.message || 'Failed to send password reset email. Please try again.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for ForgotPasswordView */
</style>