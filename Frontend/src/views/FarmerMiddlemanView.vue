<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col-md-10 offset-md-1">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4>My Farms & Support Staff</h4>
            <p class="small text-muted mb-0">Manage your farms and the personnel who help you</p>
          </div>
          <div class="card-body">
            <div v-if="isLoading" class="text-center py-5">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">Loading your operations...</p>
            </div>

            <div v-else-if="farms.length === 0" class="alert alert-info">
              <strong>No devices connected yet</strong>
              <p class="mb-0">Connect a device via OTP from the Dashboard first.</p>
              <router-link to="/dashboard" class="btn btn-primary mt-3">Go to Dashboard</router-link>
            </div>

            <div v-else>
              <div v-for="farm in farms" :key="farm.id" class="card mb-4">
                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                  <h5 class="mb-0">{{ farm.name }}</h5>
                  <span class="badge bg-primary">{{ farm.device_ids?.length || 0 }} Device(s)</span>
                </div>
                <div class="card-body">
                  <div class="row">
                    <!-- Primary Officer -->
                    <div class="col-md-6 mb-3 mb-md-0 border-end">
                      <h6 class="text-muted small text-uppercase">Primary Officer</h6>
                      <div v-if="getOfficerForFarm(farm)" class="d-flex justify-content-between align-items-center p-2 bg-light rounded">
                        <div>
                          <strong>{{ getOfficerForFarm(farm).username }}</strong><br>
                          <small class="text-muted">{{ getOfficerForFarm(farm).email }}</small>
                        </div>
                        <button class="btn btn-sm btn-outline-danger" @click="confirmRevoke(getOfficerForFarm(farm))">Revoke Access</button>
                      </div>
                      <div v-else class="text-muted italic small p-2">No primary officer assigned.</div>
                    </div>
                    
                    <!-- Middlemen -->
                    <div class="col-md-6">
                      <h6 class="text-muted small text-uppercase">Assigned Middlemen</h6>
                      <div v-if="getMiddlemenForFarm(farm).length > 0" class="list-group list-group-flush">
                        <div v-for="m in getMiddlemenForFarm(farm)" :key="m.id" class="list-group-item d-flex justify-content-between align-items-center bg-transparent px-0 py-1">
                          <div>
                            <span>{{ m.username }}</span><br>
                            <small class="text-muted">{{ m.email }}</small>
                          </div>
                          <button class="btn btn-xs text-danger p-0" @click="confirmRevoke(m)">Revoke Access</button>
                        </div>
                      </div>
                      <div v-else class="text-muted italic small p-2">No middlemen assigned.</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="alert alert-warning mt-4 small">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Note:</strong> Revoking access will immediately prevent the officer or middleman from monitoring your sensors and irrigation systems.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Revoke Confirmation Modal -->
    <div v-if="showConfirmRevoke" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Revoke Access</h5>
            <button type="button" class="btn-close" @click="showConfirmRevoke = false"></button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to revoke <strong>{{ selectedPerson?.username }}</strong>'s access?
            </p>
            <p class="text-muted small">
              They will no longer be able to see your sensors, irrigation status, or any other data for your farms.
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showConfirmRevoke = false">Cancel</button>
            <button 
              type="button" 
              class="btn btn-danger"
              @click="confirmRevokeAction"
              :disabled="isRevoking">
              <span v-if="isRevoking" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Revoke Access
            </button>
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
const personnel = ref([]);
const isLoading = ref(true);
const isRevoking = ref(false);
const showConfirmRevoke = ref(false);
const selectedPerson = ref(null);

onMounted(async () => {
  await loadData();
});

const loadData = async () => {
  isLoading.value = true;
  try {
    if (!authStore.user?.id) {
      throw new Error('User not authenticated');
    }

    // Treat each device as a farm
    const devices = await apiService.getDevices();
    farms.value = devices.map(d => ({
      id: d.id,
      name: d.name || d.id,
      location: d.location || null,
      device_ids: [d.id],
      assigned_officer_id: null,
      assigned_middleman_ids: [],
    }));

    // Load all personnel assigned to this farmer
    personnel.value = await apiService.getMiddlemanForFarmer(authStore.user.id);

  } catch (error) {
    console.error('Failed to load data:', error);
    farms.value = [];
    personnel.value = [];
  } finally {
    isLoading.value = false;
  }
};

// Since assignments are per-farmer not per-device,
// show all officers across all farms
const getOfficerForFarm = (farm) => {
  return personnel.value.find(p => p.role === 'officer') || null;
};

const getMiddlemenForFarm = (farm) => {
  return personnel.value.filter(p => p.role === 'middleman');
};

const confirmRevoke = (person) => {
  selectedPerson.value = person;
  showConfirmRevoke.value = true;
};

const confirmRevokeAction = async () => {
  if (!selectedPerson.value || !authStore.user?.id) return;

  isRevoking.value = true;
  try {
    await apiService.revokeMiddlemanFromFarmer(authStore.user.id, selectedPerson.value.id);
    await loadData();
    showConfirmRevoke.value = false;
    selectedPerson.value = null;
    alert('Access revoked successfully');
  } catch (error) {
    console.error('Failed to revoke access:', error);
    alert('Failed to revoke access. Please try again.');
  } finally {
    isRevoking.value = false;
  }
};
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.btn-xs {
  padding: 0.1rem 0.25rem;
  font-size: 0.75rem;
}

.italic {
  font-style: italic;
}
</style>
