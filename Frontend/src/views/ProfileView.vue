<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card">
          <div class="card-header">
            <h4>User Profile</h4>
          </div>
          <div class="card-body">
            <div v-if="user">
              <p><strong>Name:</strong> {{ user.username }}</p>
              <p><strong>Email:</strong> {{ user.email }}</p>
              <p><strong>Role:</strong> {{ user.role }}</p>
              <p v-if="user.full_name"><strong>Full Name:</strong> {{ user.full_name }}</p>
              <p v-if="user.location"><strong>Location:</strong> {{ user.location }}</p>
              <div v-if="user.profile_picture_url" class="mb-3">
                <strong>Profile Picture:</strong><br>
                <img :src="user.profile_picture_url" alt="Profile Picture" class="img-thumbnail mt-2" style="max-width: 150px;">
              </div>
              <div v-else class="mb-3">
                <strong>Profile Picture:</strong><br>
                <img src="/default_profile_pic.png" alt="Default Profile Picture" class="img-thumbnail mt-2" style="max-width: 150px;">
              </div>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { authStore, fetchUser } from '@/store/auth';
import { authService } from '@/services/auth'; // Import authService

const user = ref(null);
const emailVerificationMessage = ref('');
const errorMessage = ref('');
const successMessage = ref('');

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  user.value = authStore.user;
});

const confirmDeleteAccount = async () => {
  if (confirm('Are you sure you want to delete your account? This action requires email verification.')) {
    try {
      const result = await authService.sendDeleteAccountVerificationEmail();
      if (result.success) {
        emailVerificationMessage.value = 'A verification email has been sent to your email address. Please click the link in the email to confirm account deletion.';
        successMessage.value = '';
        errorMessage.value = '';
      } else {
        errorMessage.value = result.message;
        successMessage.value = '';
        emailVerificationMessage.value = '';
      }
    } catch (error) {
      console.error('Error initiating delete account verification:', error);
      errorMessage.value = error.message || 'Failed to initiate account deletion verification.';
      successMessage.value = '';
      emailVerificationMessage.value = '';
    }
  }
};
</script>

<style scoped>
/* Scoped styles for ProfileView */
</style>
