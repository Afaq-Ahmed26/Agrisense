<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-header">
        <h4>Notifications</h4>
      </div>
      <div class="card-body">
        <ul class="list-group">
          <li v-for="notification in notificationsStore.notifications" :key="notification.id" 
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
        <p v-if="notificationsStore.notifications.length === 0 && !notificationsStore.isLoading" class="text-center text-muted mt-3">You have no notifications.</p>
        <p v-if="notificationsStore.isLoading" class="text-center text-muted mt-3">Loading notifications...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { notificationsStore } from '@/store/notifications';

// Notifications are now managed by the store, fetched and updated automatically
// The component simply reacts to changes in the store.

const markAsRead = async (notification) => {
  await notificationsStore.markAsRead(notification.id);
};
</script>

<style scoped>
.list-group-item-light {
  background-color: #f8f9fa;
}
</style>
