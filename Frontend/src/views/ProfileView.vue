<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card mb-4">
          <div class="card-header">
            <h4>User Profile</h4>
          </div>
          <div class="card-body">
            <div v-if="user">
              <p><strong>Name:</strong> {{ user.username }}</p>
              <p><strong>Email:</strong> {{ user.email }}</p>
              <p><strong>Role:</strong> {{ user.role }}</p>
              <p v-if="user.full_name"><strong>Full Name:</strong> {{ user.full_name }}</p>
              <p><strong>Account Created:</strong> {{ new Date(user.created_at).toLocaleDateString() }}</p>
              <router-link to="/update-profile" class="btn btn-primary me-2">Update Profile</router-link>
              <button @click="confirmDeleteAccount" class="btn btn-danger">Delete Account</button>
            </div>
            <div v-else>
              <p>Loading user data...</p>
            </div>

            <div v-if="emailVerificationMessage" class="alert alert-info mt-3" role="alert">
                {{ emailVerificationMessage }}
            </div>
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
                {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
                {{ successMessage }}
            </div>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">
            <h4>Preferences</h4>
          </div>
          <div class="card-body">
            <form v-if="userPreferences" @submit.prevent="savePreferences">
              <div class="mb-3">
                <label for="temperatureUnit" class="form-label">Temperature Unit</label>
                <select id="temperatureUnit" class="form-select" v-model="userPreferences.temperature_unit">
                  <option value="Celsius">Celsius</option>
                  <option value="Fahrenheit">Fahrenheit</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="volumeUnit" class="form-label">Volume Unit</label>
                <select id="volumeUnit" class="form-select" v-model="userPreferences.volume_unit">
                  <option value="liters">Liters</option>
                  <option value="gallons">Gallons</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="timeZone" class="form-label">Time Zone</label>
                <input type="text" id="timeZone" class="form-control" v-model="userPreferences.time_zone">
              </div>
              <button type="submit" class="btn btn-success">Save Preferences</button>
            </form>
            <div v-else>
              <p>Loading preferences...</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h4>Notification Preferences</h4>
          </div>
          <div class="card-body">
            <form v-if="notificationPreferences" @submit.prevent="saveNotificationPreferences">
              <div class="mb-3">
                <label for="onCritical" class="form-label">Critical Alerts</label>
                <select id="onCritical" class="form-select" v-model="notificationPreferences.on_critical_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onHigh" class="form-label">High Alerts</label>
                <select id="onHigh" class="form-select" v-model="notificationPreferences.on_high_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onMedium" class="form-label">Medium Alerts</label>
                <select id="onMedium" class="form-select" v-model="notificationPreferences.on_medium_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onLow" class="form-label">Low Alerts</label>
                <select id="onLow" class="form-select" v-model="notificationPreferences.on_low_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <button type="submit" class="btn btn-success">Save Notification Settings</button>
            </form>
            <div v-else>
              <p>Loading notification preferences...</p>
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
import { authService } from '@/services/auth';
import { apiService } from '@/services/api';

const user = ref(null);
const userPreferences = ref(null);
const notificationPreferences = ref(null);
const emailVerificationMessage = ref('');
const errorMessage = ref('');
const successMessage = ref('');

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  user.value = authStore.user;
  if (user.value) {
    try {
      userPreferences.value = await apiService.getUserPreferences(user.value.id);
      notificationPreferences.value = await apiService.getUserNotificationPreferences(user.value.id);
    } catch (error) {
      console.error('Failed to load user settings:', error);
      errorMessage.value = 'Failed to load user settings.';
    }
  }
});

const savePreferences = async () => {
  if (!user.value || !userPreferences.value) return;
  try {
    await apiService.updateUserPreferences(user.value.id, userPreferences.value);
    successMessage.value = 'Preferences saved successfully!';
    errorMessage.value = '';
    // Refresh user data to update preferences in the store
    await fetchUser();
    user.value = authStore.user;
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error('Failed to save preferences:', error);
    errorMessage.value = 'Failed to save preferences.';
    successMessage.value = '';
  }
};

const saveNotificationPreferences = async () => {
  if (!user.value || !notificationPreferences.value) return;
  try {
    await apiService.updateUserNotificationPreferences(user.value.id, notificationPreferences.value);
    successMessage.value = 'Notification preferences saved successfully!';
    errorMessage.value = '';
    // Refresh user data to update preferences in the store
    await fetchUser();
    user.value = authStore.user;
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error('Failed to save notification preferences:', error);
    errorMessage.value = 'Failed to save notification preferences.';
    successMessage.value = '';
  }
};

const confirmDeleteAccount = async () => {
  if (confirm('Are you sure you want to delete your account? This action requires email verification.')) {
    try {
      const result = await authService.sendDeleteAccountVerificationEmail();
      if (result.success) {
        emailVerificationMessage.value = 'A verification email has been sent. Please click the link in the email to confirm account deletion.';
        successMessage.value = '';
        errorMessage.value = '';
      } else {
        errorMessage.value = result.message;
      }
    } catch (error) {
      console.error('Error initiating delete account verification:', error);
      errorMessage.value = error.message || 'Failed to initiate account deletion verification.';
    }
  }
};
</script>

<style scoped>
.card {
  overflow: hidden; /* Ensures inner elements don't overflow rounded corners */
}
</style>
