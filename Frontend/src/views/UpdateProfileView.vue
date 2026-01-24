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
import { updateProfile, updatePassword, reauthenticateWithCredential, EmailAuthProvider } from 'firebase/auth';
import { auth } from '@/services/firebaseConfig'; // Import Firebase auth instance

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

  if (password.value && password.value !== confirmPassword.value) {
    errorMessage.value = 'New passwords do not match.';
    isLoading.value = false;
    return;
  }

  try {
    const currentUser = auth.currentUser; // Get the current Firebase user

    if (!currentUser) {
      errorMessage.value = 'No authenticated user found.';
      isLoading.value = false;
      return;
    }

    // 1. Update Username/Display Name (if changed) - still rely on backend for 'username' for now
    // Check if the current name value is different from what's stored
    if (name.value && name.value !== (authStore.user.displayName || authStore.user.username)) {
      const payload = { username: name.value };
      // Assuming backend uses UID for user identification
      await apiService.updateUser(authStore.user.uid, payload);
      // Optionally update Firebase displayName if we want it in sync
      await updateProfile(currentUser, { displayName: name.value });
    }

    // 2. Update Password (if provided)
    if (password.value) {
      // Firebase requires recent login for password updates
      // This is a simplified approach, a real app might prompt for re-authentication
      try {
        await updatePassword(currentUser, password.value);
        successMessage.value = 'Password updated successfully! ';
      } catch (pwError) {
        if (pwError.code === 'auth/requires-recent-login') {
          errorMessage.value = 'To update your password, please log out and log in again, then try changing your password.';
          // A more robust solution would involve prompting for re-authentication here (e.g., using reauthenticateWithCredential)
        } else {
          // General Firebase Auth error for password update
          errorMessage.value = pwError.message || 'Failed to update password.';
        }
        isLoading.value = false;
        return; // Exit if password update fails
      }
    }

    successMessage.value += 'Profile updated successfully!';
    // Re-fetch user to get latest data, including potentially updated displayName/username from backend
    await fetchUser();

  } catch (error) {
    console.error('Profile update error:', error);
    errorMessage.value = error.message || 'An unexpected error occurred during profile update.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for UpdateProfileView */
</style>
