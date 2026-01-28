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
            <li class="nav-item" v-if="userRole === 'admin'">
              <router-link class="nav-link" to="/user-management" :class="{ active: currentRouteName === 'UserManagement' }"><i class="fas fa-users-cog me-1"></i>User Management</router-link>
            </li>
            <li class="nav-item" v-if="userRole === 'admin'">
              <router-link class="nav-link" to="/activity-logs" :class="{ active: currentRouteName === 'ActivityLogs' }"><i class="fas fa-clipboard-list me-1"></i>Activity Log</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/reports" :class="{ active: currentRouteName === 'Reports' }"><i class="fas fa-chart-line me-1"></i>Reports</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/notifications" :class="{ active: currentRouteName === 'Notifications' }">
                <i class="fas fa-bell me-1"></i>
                <span v-if="unreadCount > 0" class="badge rounded-pill bg-danger">
                  {{ unreadCount }}
                </span>
              </router-link>
            </li>
            <!-- Add other nav items here as needed for Analytics, Settings, etc. -->
          </ul>
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                <i class="fas fa-user me-1"></i><span>{{ userName }} ({{ userRole }})</span>
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><router-link class="dropdown-item" to="/profile"><i class="fas fa-user-circle me-2"></i>Profile</router-link></li>
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
import { computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authService } from '@/services/auth';
import { authStore, isAuthenticated } from '@/store/auth';
import { notificationsStore } from '@/store/notifications';

const router = useRouter();
const route = useRoute();

const currentRouteName = computed(() => route.name);

const userName = computed(() => {
  return authStore.user?.username || authStore.user?.email?.split('@')[0] || 'User';
});

const userRole = computed(() => {
  return authStore.user?.role || '';
});

const unreadCount = computed(() => notificationsStore.unreadCount);

onMounted(() => {
  if (isAuthenticated.value) {
    notificationsStore.fetchNotifications();
    notificationsStore.startPolling();
  }
});

onUnmounted(() => {
  notificationsStore.stopPolling();
});

const logout = async () => {
  await authService.logout();
  notificationsStore.stopPolling(); // Stop polling on logout
  router.push('/login');
};
</script>

<style>
/* Global styles */
</style>