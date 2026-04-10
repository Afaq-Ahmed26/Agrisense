import { reactive, computed } from 'vue';
import { apiService } from '@/services/api';

export const notificationsStore = reactive({
  notifications: [],
  isLoading: false,
  error: null,
  filterArchived: false, // NEW
  currentPage: 1, // NEW
  itemsPerPage: 10, // NEW
  totalCount: 0, // NEW (this will be estimated for now as API doesn't return total)
  lastPageFetched: 0, // NEW

  get unreadCount() {
    return this.notifications.filter(n => !n.is_read && !n.is_archived).length; // Updated logic
  },

  async fetchNotifications({ isArchived = false, currentPage = 1, itemsPerPage = 10 } = {}) { // Modified
    this.isLoading = true;
    this.error = null;
    try {
      const skip = (currentPage - 1) * itemsPerPage;
      const fetchedNotifications = await apiService.getNotifications(isArchived, skip, itemsPerPage);
      this.notifications = fetchedNotifications;
      // For now, estimate totalCount based on whether we filled the last page
      this.totalCount = (fetchedNotifications.length < itemsPerPage && currentPage > 1) 
                        ? (currentPage - 1) * itemsPerPage + fetchedNotifications.length
                        : currentPage * itemsPerPage + 1; // Arbitrarily set to allow next page until actual total is known
      this.currentPage = currentPage;
      this.itemsPerPage = itemsPerPage;
      this.filterArchived = isArchived;
      this.lastPageFetched = currentPage;
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
        this.notifications[index] = { ...this.notifications[index], ...updatedNotification }; // Merge updates
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  },

  // NEW
  async archiveNotification(notificationId) {
    try {
      const updatedNotification = await apiService.archiveNotification(notificationId);
      const index = this.notifications.findIndex(n => n.id === notificationId);
      if (index !== -1) {
        this.notifications[index] = { ...this.notifications[index], ...updatedNotification }; // Merge updates
      }
      // Re-fetch notifications if the filter is set to show active, to remove the archived one
      if (!this.filterArchived) {
        this.fetchNotifications({ isArchived: this.filterArchived, currentPage: this.currentPage, itemsPerPage: this.itemsPerPage });
      }
    } catch (err) {
      console.error('Failed to archive notification:', err);
    }
  },

  // NEW
  async unarchiveNotification(notificationId) {
    try {
      const updatedNotification = await apiService.unarchiveNotification(notificationId);
      const index = this.notifications.findIndex(n => n.id === notificationId);
      if (index !== -1) {
        this.notifications[index] = { ...this.notifications[index], ...updatedNotification }; // Merge updates
      }
      // Re-fetch notifications if the filter is set to show archived, to remove the unarchived one
      if (this.filterArchived) {
        this.fetchNotifications({ isArchived: this.filterArchived, currentPage: this.currentPage, itemsPerPage: this.itemsPerPage });
      }
    } catch (err) {
      console.error('Failed to unarchive notification:', err);
    }
  },

  startPolling(interval = 300000) { // Poll every 5 minutes (300,000 ms)
    if (this.pollingId) {
      this.stopPolling();
    }
    // Only poll if on the first page and not showing archived (to keep UI responsive to archive actions)
    if (this.currentPage === 1 && !this.filterArchived) {
        this.pollingId = setInterval(() => {
            this.fetchNotifications({ isArchived: this.filterArchived, currentPage: this.currentPage, itemsPerPage: this.itemsPerPage });
        }, interval);
    }
  },

  stopPolling() {
    if (this.pollingId) {
      clearInterval(this.pollingId);
      this.pollingId = null;
    }
  },

  // NEW: Add a client-side notification
  addNotification({ title, message, type = 'info', deviceId = null }) {
    const newNotification = {
      id: `client_generated_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title: title,
      message: message,
      type: type,
      device_id: deviceId,
      is_read: false,
      is_archived: false,
      timestamp: new Date().toISOString()
    };
    this.notifications.unshift(newNotification); // Add to the beginning of the array
    // Optionally, if we want to limit client-side notifications
    // if (this.notifications.length > 50) {
    //   this.notifications.pop();
    // }
  }
});
