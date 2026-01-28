<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h4>Activity Log</h4>
          </div>
          <div class="card-body">
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
                    <td>{{ formatDetails(log.details) }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-if="activityLogs.length === 0" class="text-center text-muted mt-3">No activity logs found.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiService } from '@/services/api';

const activityLogs = ref([]);
const isLoading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    activityLogs.value = await apiService.getActivityLogs();
  } catch (err) {
    console.error('Failed to fetch activity logs:', err);
    error.value = err.message || 'An error occurred while fetching activity logs.';
  } finally {
    isLoading.value = false;
  }
});

const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

const formatDetails = (details) => {
  if (!details) return '-';
  return JSON.stringify(details, null, 2);
};
</script>

<style scoped>
/* Optional: Add custom styles here if needed */
</style>
