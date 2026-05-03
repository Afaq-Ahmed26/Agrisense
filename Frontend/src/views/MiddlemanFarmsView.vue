<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4>Your Assigned Farmers & Farms</h4>
            <p class="small text-muted mb-0">Operations you have been assigned to manage</p>
          </div>
          <div class="card-body">
            <div v-if="isLoading" class="text-center py-5">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">Loading assignments...</p>
            </div>

            <div v-else-if="farmers.length === 0" class="alert alert-info">
              <strong>No farmers assigned</strong>
              <p class="mb-0">You have not been assigned to any farmers yet. Contact your admin for assignment.</p>
            </div>

            <div v-else>
              <div v-for="farmer in farmers" :key="farmer.id" class="card mb-4 border-primary">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                  <h5 class="mb-0">
                    <i class="fas fa-user me-2"></i>{{ farmer.username }}
                  </h5>
                  <span>{{ farmer.email }}</span>
                </div>
                <div class="card-body">
                  <div v-if="getFarmsForFarmer(farmer.id).length === 0" class="text-muted italic">
                     This farmer has no devices connected yet.
                  </div>
                  <div v-else class="table-responsive">
                    <table class="table table-hover mb-0">
                      <thead class="table-light">
                        <tr>
                          <th>Farm Name</th>
                          <th>Location</th>
                          <th>Devices</th>
                          <th>Role</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="farm in getFarmsForFarmer(farmer.id)" :key="farm.id">
                          <td><strong>{{ farm.name }}</strong></td>
                          <td>{{ farm.location || 'N/A' }}</td>
                          <td>
                            <span v-if="farm.device_ids?.length > 0" class="badge bg-info text-dark">
                              {{ farm.device_ids.length }} device(s)
                            </span>
                            <span v-else class="text-muted small">None</span>
                          </td>
                          <td>
                            <span class="badge bg-success">Assigned</span>
                          
                            
                          </td>
                          <td>
                            <router-link 
                              :to="{ name: 'Dashboard', query: { deviceId: (farm.device_ids?.length > 0) ? farm.device_ids[0] : null } }"
                              class="btn btn-sm btn-primary">
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiService } from '@/services/api';
import { authStore } from '@/store/auth';

const farmers = ref([]);
const farmerDevices = ref({}); // keyed by farmer.id
const isLoading = ref(true);

onMounted(async () => {
  await loadData();
});

const loadData = async () => {
  isLoading.value = true;
  try {
    if (!authStore.user?.id) {
      throw new Error('User not authenticated');
    }

    // 1. Load farmers assigned to this officer
    farmers.value = await apiService.getFarmersForMiddleman(authStore.user.id);

    // 2. For each farmer, load their devices and treat each as a farm
    const deviceMap = {};
    for (const farmer of farmers.value) {
      try {
        // Temporarily switch to farmer context isn't possible,
        // so use getFarmsForMiddleman which returns virtual farms per farmer
        const farmsData = await apiService.getFarmsForMiddleman(authStore.user.id);
        deviceMap[farmer.id] = farmsData
          .filter(f => f.owner_id === farmer.id)
          .map(f => ({
            id: f.id,
            name: f.name || f.id,
            location: f.location || null,
            device_ids: f.device_ids || [f.id],
            assigned_officer_id: f.assigned_officer_id,
            assigned_middleman_ids: f.assigned_middleman_ids || [],
            owner_id: f.owner_id,
          }));
      } catch (e) {
        deviceMap[farmer.id] = [];
      }
    }
    farmerDevices.value = deviceMap;

  } catch (error) {
    console.error('Failed to load assignment data:', error);
  } finally {
    isLoading.value = false;
  }
};

const getFarmsForFarmer = (farmerId) => {
  return farmerDevices.value[farmerId] || [];
};
</script>

<style scoped>
.italic {
  font-style: italic;
}
.card-header h5 {
  font-size: 1.1rem;
}
</style>
