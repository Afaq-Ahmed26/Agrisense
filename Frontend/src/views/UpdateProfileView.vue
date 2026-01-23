<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">
            <h4>Update Profile</h4>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleUpdate">
              <div class="mb-3">
                <label for="name" class="form-label">Full Name</label>
                <input type="text" class="form-control" id="name" v-model="name" required>
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">New Password</label>
                <input type="password" class="form-control" id="password" v-model="password">
                <small class="form-text text-muted">Leave blank to keep your current password.</small>
              </div>
              <div class="mb-3">
                <label for="confirmPassword" class="form-label">Confirm New Password</label>
                <input type="password" class="form-control" id="confirmPassword" v-model="confirmPassword">
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary" :disabled="isLoading">
                  <span v-if="isLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  Update Profile
                </button>
              </div>
            </form>
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
import { ref, onMounted } from 'vue';
import { authStore, fetchUser } from '@/store/auth';
import { apiService } from '@/services/api';

const name = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  if (authStore.user) {
    name.value = authStore.user.username;
  }
});

const handleUpdate = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.';
    isLoading.value = false;
    return;
  }

  try {
    const payload = { username: name.value };
    if (password.value) {
      payload.password = password.value;
    }

    await apiService.updateUser(authStore.user.id, payload);
    successMessage.value = 'Profile updated successfully!';
    // Optionally, refetch user data to update the store
    await fetchUser();
  } catch (error) {
    errorMessage.value = error.message || 'An unexpected error occurred during profile update.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for UpdateProfileView */
</style>
