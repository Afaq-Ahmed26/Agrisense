import { reactive, computed } from 'vue';
import { apiService } from '@/services/api';

export const notificationsStore = reactive({
  notifications: [],
  isLoading: false,
  error: null,

  get unreadCount() {
    return this.notifications.filter(n => !n.is_read).length;
  },

  async fetchNotifications() {
    this.isLoading = true;
    this.error = null;
    try {
      this.notifications = await apiService.getNotifications();
    } catch (err) {
      this.error = 'Failed to fetch notifications.';
      console.error(err);
    } finally {
      this.isLoading = false;
    }
  },

  async markAsRead(notificationId) {
    try {
      const updatedNotification = await apiService.markNotificationAsRead(notificationId);
      const index = this.notifications.findIndex(n => n.id === notificationId);
      if (index !== -1) {
        this.notifications[index] = updatedNotification;
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  },

  startPolling(interval = 30000) { // Poll every 30 seconds
    if (this.pollingId) {
      this.stopPolling();
    }
    this.pollingId = setInterval(() => {
      this.fetchNotifications();
    }, interval);
  },

  stopPolling() {
    if (this.pollingId) {
      clearInterval(this.pollingId);
      this.pollingId = null;
    }
  }
});
