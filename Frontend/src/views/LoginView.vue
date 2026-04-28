<template>
  <div class="container">
    <div class="row justify-content-center align-items-center min-vh-100">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-3">
          <div class="card-header text-center bg-primary text-white py-4 rounded-top-3">
            <h2 class="mb-0"><i class="fas fa-seedling me-2"></i>AgriSense</h2>
            <small class="opacity-75">Smart Irrigation Management</small>
          </div>
          <div class="card-body p-4">
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="email" class="form-label">Email Address</label>
                <input type="email" class="form-control" id="email" v-model="email" placeholder="Enter your email" required>
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" v-model="password" placeholder="Enter your password" required>
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg" :disabled="isLoading">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  Login
                </button>
              </div>
            </form>
            
            <div class="text-center mt-3">
              <router-link to="/register" class="text-decoration-none">Don't have an account? Register here</router-link>
            </div>
            <div class="text-center mt-2">
              <router-link to="/forgot-password" class="text-decoration-none">Forgot Password?</router-link>
            </div>
            
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
              {{ errorMessage }}
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
import { authService } from '@/services/auth';

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);
const router = useRouter();

const handleLogin = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  const result = await authService.login(email.value, password.value);
  if (result.success) {
    if (result.requiresVerification) {
      router.push({ name: 'VerifyEmail', query: { email: result.email || email.value } });
    } else {
      router.push('/dashboard');
    }
  } else {
    errorMessage.value = result.message;
  }
  isLoading.value = false;
};
</script>

<style scoped>
/* Scoped styles for LoginView */
</style>
