<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col-md-8 offset-md-2">
        <div class="card">
          <div class="card-header">
            <h4>Middlemen Access Management</h4>
            <p class="small text-muted mb-0">Manage which middlemen/officers have access to your farms</p>
          </div>
          <div class="card-body">
            <div v-if="isLoading" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>

            <div v-else-if="middlemen.length === 0" class="alert alert-info">
              <strong>No middlemen assigned</strong>
              <p class="mb-0">Your admin can assign middlemen to help you manage your farms.</p>
            </div>

            <div v-else>
              <p class="text-muted">These middlemen have access to your farms and can monitor irrigation, sensors, and help you manage your operations:</p>
              
              <div class="list-group">
                <div v-for="middleman in middlemen" :key="middleman.id" class="list-group-item">
                  <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                      <h5 class="mb-1">{{ middleman.username }}</h5>
                      <p class="mb-1 text-muted">{{ middleman.email }}</p>
                      <small class="text-muted">Role: {{ middleman.role }}</small>
                    </div>
                    <button 
                      class="btn btn-outline-danger btn-sm"
                      @click="confirmRevoke(middleman)"
                      :disabled="isRevoking">
                      <span v-if="isRevoking && revokingMiddlemanId === middleman.id" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                      Revoke Access
                    </button>
                  </div>
                </div>
              </div>

              <div class="alert alert-warning mt-4 small">
                <strong>Note:</strong> Revoking access will immediately prevent this middleman from viewing or managing your farms.
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
              Are you sure you want to revoke <strong>{{ selectedMiddleman?.username }}</strong>'s access to your farms?
            </p>
            <p class="text-muted small">
              They will no longer be able to see your sensors, irrigation status, or any other farm data.
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

const middlemen = ref([]);
const isLoading = ref(true);
const isRevoking = ref(false);
const revokingMiddlemanId = ref(null);
const showConfirmRevoke = ref(false);
const selectedMiddleman = ref(null);

onMounted(async () => {
  await loadMiddlemen();
});

const loadMiddlemen = async () => {
  isLoading.value = true;
  try {
    if (!authStore.user?.id) {
      throw new Error('User not authenticated');
    }
    
    middlemen.value = await apiService.getMiddlemanForFarmer(authStore.user.id);
  } catch (error) {
    console.error('Failed to load middlemen:', error);
    middlemen.value = [];
    alert('Failed to load middlemen. Please try again.');
  } finally {
    isLoading.value = false;
  }
};

const confirmRevoke = (middleman) => {
  selectedMiddleman.value = middleman;
  showConfirmRevoke.value = true;
};

const confirmRevokeAction = async () => {
  if (!selectedMiddleman.value || !authStore.user?.id) {
    return;
  }

  isRevoking.value = true;
  revokingMiddlemanId.value = selectedMiddleman.value.id;

  try {
    await apiService.revokeMiddlemanFromFarmer(authStore.user.id, selectedMiddleman.value.id);
    
    // Remove from list
    middlemen.value = middlemen.value.filter(m => m.id !== selectedMiddleman.value.id);
    
    // Close modal
    showConfirmRevoke.value = false;
    selectedMiddleman.value = null;
    
    alert(`${selectedMiddleman.value.username}'s access has been revoked`);
  } catch (error) {
    console.error('Failed to revoke middleman:', error);
    alert('Failed to revoke access. Please try again.');
  } finally {
    isRevoking.value = false;
    revokingMiddlemanId.value = null;
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

.list-group-item {
  padding: 1rem;
  border: 1px solid #e0e0e0;
  margin-bottom: 0.5rem;
  border-radius: 0.25rem;
}

.list-group-item:last-child {
  margin-bottom: 0;
}
</style>
