<template>
  <div class="container mt-5">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h4>Notifications</h4>
        <div class="form-check form-switch">
          <input class="form-check-input" type="checkbox" id="showArchivedSwitch" v-model="notificationsStore.filterArchived" @change="notificationsStore.currentPage = 1">
          <label class="form-check-label" for="showArchivedSwitch">Show Archived</label>
        </div>
      </div>
      <div class="card-body">
        <div v-if="notificationsStore.isLoading" class="text-center">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p>Loading notifications...</p>
        </div>
        <div v-else-if="notificationsStore.error" class="alert alert-danger" role="alert">
          {{ notificationsStore.error }}
        </div>
        <ul class="list-group" v-else-if="notificationsStore.notifications.length > 0">
          <li v-for="notification in notificationsStore.notifications" :key="notification.id" 
              class="list-group-item d-flex justify-content-between align-items-center"
              :class="{ 'list-group-item-light': notification.is_read }">
            
            <div>
              <p class="mb-1">{{ notification.message }}</p>
              <small class="text-muted">{{ new Date(notification.created_at).toLocaleString() }}</small>
            </div>

            <div class="btn-group">
              <button v-if="!notification.is_read" 
                      @click="markAsRead(notification.id)" 
                      class="btn btn-sm btn-outline-primary me-2">
                Mark as Read
              </button>
              <button v-if="!notification.is_archived"
                      @click="archiveNotification(notification.id)"
                      class="btn btn-sm btn-outline-secondary me-2">
                Archive
              </button>
              <button v-else
                      @click="unarchiveNotification(notification.id)"
                      class="btn btn-sm btn-outline-info me-2">
                Unarchive
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="text-center text-muted mt-3">You have no notifications.</p>

        <!-- Pagination -->
        <nav aria-label="Notification Pagination" class="mt-3" v-if="notificationsStore.notifications.length > 0 || notificationsStore.currentPage > 1">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: notificationsStore.currentPage === 1 }">
              <button class="page-link" @click="prevPage" :disabled="notificationsStore.currentPage === 1">Previous</button>
            </li>
            <li class="page-item disabled">
              <span class="page-link">Page {{ notificationsStore.currentPage }}</span>
            </li>
            <li class="page-item" :class="{ disabled: notificationsStore.notifications.length < notificationsStore.itemsPerPage }">
              <button class="page-link" @click="nextPage" :disabled="notificationsStore.notifications.length < notificationsStore.itemsPerPage">Next</button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { notificationsStore } from '@/store/notifications';

const markAsRead = async (notificationId) => {
  await notificationsStore.markAsRead(notificationId);
};

const archiveNotification = async (notificationId) => {
  await notificationsStore.archiveNotification(notificationId);
};

const unarchiveNotification = async (notificationId) => {
  await notificationsStore.unarchiveNotification(notificationId);
};

const nextPage = () => {
  if (notificationsStore.notifications.length === notificationsStore.itemsPerPage) {
    notificationsStore.currentPage++;
  }
};

const prevPage = () => {
  if (notificationsStore.currentPage > 1) {
    notificationsStore.currentPage--;
  }
};

onMounted(() => {
  notificationsStore.fetchNotifications({ 
    isArchived: notificationsStore.filterArchived, 
    currentPage: notificationsStore.currentPage, 
    itemsPerPage: notificationsStore.itemsPerPage 
  });
});

watch(
  () => [notificationsStore.currentPage, notificationsStore.filterArchived],
  () => {
    notificationsStore.fetchNotifications({ 
      isArchived: notificationsStore.filterArchived, 
      currentPage: notificationsStore.currentPage, 
      itemsPerPage: notificationsStore.itemsPerPage 
    });
  }
);
</script>

<style scoped>
.list-group-item-light {
  background-color: #f8f9fa;
}
</style>
