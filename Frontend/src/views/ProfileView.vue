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
              <p><strong>Account Created:</strong> {{ new Date(user.created_at).toLocaleDateString() }}</p>
              <router-link to="/update-profile" class="btn btn-primary">Update Profile</router-link>
            </div>
            <div v-else>
              <p>Loading user data...</p>
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

const user = ref(null);

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  user.value = authStore.user;
});
</script>

<style scoped>
/* Scoped styles for ProfileView */
</style>
