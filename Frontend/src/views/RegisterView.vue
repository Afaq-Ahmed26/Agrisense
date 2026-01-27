<template>
  <div class="container">
    <div class="row justify-content-center align-items-center min-vh-100">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow-lg border-0 rounded-3">
          <div class="card-header text-center bg-success text-white py-4 rounded-top-3">
            <h2 class="mb-0"><i class="fas fa-user-plus me-2"></i>Create Account</h2>
            <small class="opacity-75">Join the AgriSense community</small>
          </div>
          <div class="card-body p-4">
            <form @submit.prevent="handleRegister">
              <div class="mb-3">
                <label for="name" class="form-label">Full Name</label>
                <input type="text" class="form-control" id="name" v-model="name" placeholder="Enter your full name" required>
              </div>
              <div class="mb-3">
                <label for="email" class="form-label">Email Address</label>
                <input type="email" class="form-control" id="email" v-model="email" placeholder="Enter your email" required>
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">Password</label>
                <input type="password" class="form-control" id="password" v-model="password" placeholder="Enter your password" required>
              </div>
              <div class="mb-3">
                <label for="confirmPassword" class="form-label">Confirm Password</label>
                <input type="password" class="form-control" id="confirmPassword" v-model="confirmPassword" placeholder="Confirm your password" required>
              </div>

              <div class="mb-3">
                <label for="role" class="form-label">Select Role</label>
                <select class="form-select" id="role" v-model="role" required>
                  <option value="">Choose your role...</option>
                  <option value="farmer">Farmer</option>
                  <option value="officer">Officer</option>
                </select>
              </div>

              <div class="d-grid">
                <button type="submit" class="btn btn-success btn-lg" :disabled="isLoading">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  Register
                </button>
              </div>
            </form>
            
            <div class="text-center mt-3">
              <router-link to="/login" class="text-decoration-none">Already have an account? Login here</router-link>
            </div>
            
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
              {{ errorMessage }}
            </div>
             <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
              {{ successMessage }}
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

const name = ref('');
const email = ref('');
const password = ref('');
const confirmPassword = ref('');
const role = ref('');

const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);
const router = useRouter();

const handleRegister = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.';
    isLoading.value = false;
    return;
  }

  const userData = {
    email: email.value,
    password: password.value,
    username: name.value, // Changed 'name' to 'username'
    role: role.value,

  };

  const result = await authService.register(userData);
  if (result.success) {
    successMessage.value = 'Registration successful! Redirecting to login...';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } else {
    errorMessage.value = result.message;
  }
  isLoading.value = false;
};
</script>

<style scoped>
/* Scoped styles for RegisterView */
</style>
