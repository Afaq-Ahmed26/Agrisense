<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-header">
        <h4>Notifications</h4>
      </div>
      <div class="card-body">
        <ul class="list-group">
          <li v-for="notification in notifications" :key="notification.id" 
              class="list-group-item d-flex justify-content-between align-items-center"
              :class="{ 'list-group-item-light': notification.is_read }">
            
            <div>
              <p class="mb-1">{{ notification.message }}</p>
              <small class="text-muted">{{ new Date(notification.created_at).toLocaleString() }}</small>
            </div>

            <button v-if="!notification.is_read" 
                    @click="markAsRead(notification)" 
                    class="btn btn-sm btn-outline-primary">
              Mark as Read
            </button>
          </li>
        </ul>
        <p v-if="notifications.length === 0" class="text-center text-muted mt-3">You have no notifications.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiService } from '@/services/api';

const notifications = ref([]);
const isLoading = ref(false);

onMounted(async () => {
  isLoading.value = true;
  try {
    notifications.value = await apiService.getNotifications();
  } catch (error) {
    console.error("Failed to fetch notifications:", error);
  } finally {
    isLoading.value = false;
  }
});

const markAsRead = async (notification) => {
  notification.is_read = true; // Optimistic update
  try {
    await apiService.markNotificationAsRead(notification.id);
  } catch (error) {
    console.error(`Failed to mark notification ${notification.id} as read:`, error);
    notification.is_read = false; // Revert on failure
  }
};
</script>

<style scoped>
.list-group-item-light {
  background-color: #f8f9fa;
}
</style>
