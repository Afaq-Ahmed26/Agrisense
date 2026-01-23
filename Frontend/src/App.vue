<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-success" v-if="isAuthenticated && currentRouteName !== 'Login' && currentRouteName !== 'Register'">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/dashboard"><i class="fas fa-seedling me-2"></i>AgriSense</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/dashboard" :class="{ active: currentRouteName === 'Dashboard' }"><i class="fas fa-home me-1"></i>Dashboard</router-link>
            </li>
            <!-- Add other nav items here as needed for Analytics, Settings, etc. -->
          </ul>
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                <i class="fas fa-user me-1"></i><span id="userName">{{ userName }}</span>
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><a class="dropdown-item" href="#"><i class="fas fa-user-circle me-2"></i>Profile</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" @click.prevent="logout"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authService } from '@/services/auth';

const router = useRouter();
const route = useRoute();
const userName = ref('User');
const isAuthenticated = ref(false);

const currentRouteName = computed(() => route.name);

onMounted(() => {
  // Initial check for authentication status
  isAuthenticated.value = authService.isAuthenticated();
  updateUserName();

  // Listen for changes in authentication status (e.g., after login/logout)
  authService.onAuthStateChanged(() => {
    isAuthenticated.value = authService.isAuthenticated();
    updateUserName();
  });
});

const updateUserName = () => {
  const user = authService.getCurrentUser();
  if (user) {
    userName.value = user.name || user.email.split('@')[0];
  } else {
    userName.value = 'User';
  }
};

const logout = async () => {
  try {
    await authService.logout();
    router.push('/login');
  } catch (error) {
    console.error('Logout error:', error);
    // Optionally, show a toast or alert for logout failure
  }
};
</script>

<style>
/* Global styles */
</style>