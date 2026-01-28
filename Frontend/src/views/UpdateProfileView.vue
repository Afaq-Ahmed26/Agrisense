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
                <label for="email" class="form-label">Email Address</label>
                <input type="email" class="form-control" id="email" v-model="email" required>
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
import { updateProfile, updatePassword, updateEmail, reauthenticateWithCredential, EmailAuthProvider } from 'firebase/auth';
import { firebaseService } from '@/services/firebase'; // Import firebaseService

const name = ref('');
const email = ref(''); // New email ref
const password = ref('');
const confirmPassword = ref('');
const full_name = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const isLoading = ref(false);

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  if (authStore.user) {
    name.value = authStore.user.username;
    email.value = authStore.user.email; // Initialize email field
    full_name.value = authStore.user.full_name || '';
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
    const currentUser = firebaseService.auth.currentUser; // Get the current Firebase user using firebaseService

    if (!currentUser) {
      errorMessage.value = 'No authenticated user found.';
      isLoading.value = false;
      return;
    }

    const payload = {};
    let firebaseAuthUpdated = false;

    // 1. Update Username/Display Name
    if (name.value && name.value !== authStore.user.username) {
      payload.username = name.value;
      await updateProfile(currentUser, { displayName: name.value }); // Update Firebase display name
      firebaseAuthUpdated = true;
    }

    // 2. Update Email
    if (email.value && email.value !== authStore.user.email) {
      payload.email = email.value;
      try {
        await updateEmail(currentUser, email.value);
        firebaseAuthUpdated = true;
      } catch (emailError) {
        if (emailError.code === 'auth/requires-recent-login') {
          errorMessage.value = 'To change your email, please re-authenticate by logging in again and trying the update.';
          // More robust solution would involve prompting for re-authentication here (e.g., using reauthenticateWithCredential)
        } else {
          errorMessage.value = emailError.message || 'Failed to update email.';
        }
        isLoading.value = false;
        return;
      }
    }

    // 3. Update Password
    if (password.value) {
      payload.password = password.value;
      try {
        await updatePassword(currentUser, password.value);
        firebaseAuthUpdated = true;
      } catch (pwError) {
        if (pwError.code === 'auth/requires-recent-login') {
          errorMessage.value = 'To update your password, please re-authenticate by logging in again and trying the update.';
        } else {
          errorMessage.value = pwError.message || 'Failed to update password.';
        }
        isLoading.value = false;
        return;
      }
    }
    
    // 4. Update Full Name
    if (full_name.value !== authStore.user.full_name) {
      payload.full_name = full_name.value;
    }
    
    // Send updates to backend API if there are changes beyond what Firebase Auth handles directly
    if (Object.keys(payload).length > 0) {
      // Assuming backend uses UID for user identification
      await apiService.updateUser(authStore.user.id, payload); // Use authStore.user.id (UID)
    }

    successMessage.value = 'Profile updated successfully!';
    // Re-fetch user to get latest data, including potentially updated fields from backend and Firebase Auth
    await fetchUser();

    // Clear password fields after successful update
    password.value = '';
    confirmPassword.value = '';

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
