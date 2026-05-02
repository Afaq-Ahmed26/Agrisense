<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">
            <h4>Assigned Farms</h4>
            <p class="small text-muted mb-0">Farms you have been assigned to manage</p>
          </div>
          <div class="card-body">
            <div v-if="isLoading" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>

            <div v-else-if="farms.length === 0" class="alert alert-info">
              <strong>No farms assigned</strong>
              <p class="mb-0">You have not been assigned to manage any farms yet. Contact your admin for assignment.</p>
            </div>

            <div v-else class="table-responsive">
              <table class="table table-hover">
                <thead class="table-light">
                  <tr>
                    <th>Farm Name</th>
                    <th>Owner</th>
                    <th>Devices</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="farm in farms" :key="farm.id">
                    <td>
                      <strong>{{ farm.name }}</strong>
                    </td>
                    <td>
                      {{ farm.owner_name || farm.owner_id }}
                      <br v-if="farm.owner_email">
                      <small class="text-muted" v-if="farm.owner_email">{{ farm.owner_email }}</small>
                    </td>
                    <td>
                      <span v-if="farm.device_ids && farm.device_ids.length > 0" class="badge bg-primary">
                        {{ farm.device_ids.length }} device(s)
                      </span>
                      <span v-else class="text-muted">No devices</span>
                    </td>
                    <td>
                      <router-link 
                        :to="{ name: 'Dashboard', query: { deviceId: (farm.device_ids && farm.device_ids.length > 0) ? farm.device_ids[0] : null } }"
                        class="btn btn-sm btn-outline-primary">
                        View Dashboard
                      </router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
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
import { authStore } from '@/store/auth';

const farms = ref([]);
const isLoading = ref(true);

onMounted(async () => {
  await loadFarms();
});

const loadFarms = async () => {
  isLoading.value = true;
  try {
    if (!authStore.user?.id) {
      throw new Error('User not authenticated');
    }

    // Check if user is a middleman/officer
    if (authStore.user.role !== 'officer' && authStore.user.role !== 'middleman') {
      throw new Error('This view is only accessible to middlemen/officers');
    }

    const fetchedFarms = await apiService.getFarmsForMiddleman(authStore.user.id);
    
    // Fetch owner details for each farm to show names instead of IDs
    const farmsWithOwners = await Promise.all(fetchedFarms.map(async (farm) => {
      try {
        // Use user endpoint to get owner details
        const owner = await apiService.request(`/users/${farm.owner_id}`);
        return {
          ...farm,
          owner_name: owner.username || owner.email,
          owner_email: owner.email
        };
      } catch (e) {
        console.warn(`Could not fetch details for owner ${farm.owner_id}:`, e);
        return { ...farm, owner_name: 'Unknown Owner', owner_email: '' };
      }
    }));

    farms.value = farmsWithOwners;
  } catch (error) {
    console.error('Failed to load farms:', error);
    farms.value = [];
    alert('Failed to load assigned farms. Please try again.');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.table-hover tbody tr:hover {
  background-color: #f8f9fa;
}
</style>
