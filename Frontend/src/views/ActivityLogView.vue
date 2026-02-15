<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h4>Activity Log</h4>
          </div>
          <div class="card-body">
            <div class="filters mb-3">
              <div class="row g-3">
                <div class="col-md-4">
                  <label for="userFilter" class="form-label visually-hidden">Filter by User</label>
                  <select id="userFilter" class="form-select" v-model="userFilter" @change="currentPage = 1">
                    <option value="">All Users</option>
                    <option v-for="user in usersList" :key="user.id" :value="user.id">{{ user.username }}</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label for="actionFilter" class="form-label visually-hidden">Filter by Action</label>
                  <select id="actionFilter" class="form-select" v-model="actionFilter" @change="currentPage = 1">
                    <option value="">All Actions</option>
                    <option v-for="action in actionsList" :key="action" :value="action">{{ action }}</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <button class="btn btn-secondary w-100" @click="resetFilters">Reset Filters</button>
                </div>
              </div>
            </div>

            <div v-if="isLoading" class="text-center">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p>Loading activity logs...</p>
            </div>
            <div v-else-if="error" class="alert alert-danger" role="alert">
              {{ error }}
            </div>
            <div v-else>
              <div class="table-responsive">
                <table class="table table-striped table-hover">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>User ID</th>
                      <th>Action</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="log in activityLogs" :key="log.id">
                      <td>{{ formatDate(log.timestamp) }}</td>
                      <td>{{ log.user_id }}</td>
                      <td>{{ log.action }}</td>
                      <td>
                        <pre class="mb-0">{{ formatDetails(log.details) }}</pre>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-if="activityLogs.length === 0" class="text-center text-muted mt-3">No activity logs found with current filters.</p>

              <!-- Pagination -->
              <nav aria-label="Activity Log Pagination" class="mt-3" v-if="activityLogs.length > 0">
                <ul class="pagination justify-content-center">
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <button class="page-link" @click="prevPage" :disabled="currentPage === 1">Previous</button>
                  </li>
                  <li class="page-item disabled">
                    <span class="page-link">Page {{ currentPage }}</span>
                  </li>
                  <li class="page-item" :class="{ disabled: activityLogs.length < itemsPerPage }">
                    <button class="page-link" @click="nextPage" :disabled="activityLogs.length < itemsPerPage">Next</button>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { apiService } from '@/services/api';

const activityLogs = ref([]);
const isLoading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const itemsPerPage = ref(10); // Fetch 10 items per page
const userFilter = ref('');
const actionFilter = ref('');
const usersList = ref([]); // To populate the user filter dropdown
const actionsList = ref(['User Login', 'User Logout', 'User Profile Update', 'Notification Preferences Update', 'Alert Thresholds Update', 'User Registration', 'User Deletion', 'Device Connection', 'Irrigation Start', 'Irrigation Stop']);


const fetchUsers = async () => {
  try {
    const users = await apiService.getUsers();
    usersList.value = users;
  } catch (err) {
    console.error('Failed to fetch users for filter:', err);
    // Optionally, set an error message or handle gracefully
  }
};

const fetchLogs = async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const skip = (currentPage.value - 1) * itemsPerPage.value;
    activityLogs.value = await apiService.getActivityLogs(skip, itemsPerPage.value, userFilter.value, actionFilter.value);
  } catch (err) {
    console.error('Failed to fetch activity logs:', err);
    error.value = err.message || 'An error occurred while fetching activity logs.';
  } finally {
    isLoading.value = false;
  }
};

const nextPage = () => {
  if (activityLogs.value.length === itemsPerPage.value) {
    currentPage.value++;
  }
};

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
};

const resetFilters = () => {
  userFilter.value = '';
  actionFilter.value = '';
  currentPage.value = 1;
};

onMounted(async () => {
  await fetchUsers(); // Fetch users for the filter dropdown
  await fetchLogs();
});

// Watch for changes in filters or current page to re-fetch logs
watch([currentPage, userFilter, actionFilter], fetchLogs);

const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

const formatDetails = (details) => {
  if (!details) return '-';
  // Attempt to pretty-print JSON, otherwise return as string
  try {
    return JSON.stringify(details, null, 2);
  } catch (e) {
    return String(details);
  }
};
</script>

<style scoped>
/* Optional: Add custom styles here if needed */
pre {
  white-space: pre-wrap; /* Ensures details wrap within the table cell */
  word-break: break-all;
}
</style>
