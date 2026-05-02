<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-8">
        <div class="card mb-4">
          <div class="card-header">
            <h4>User Profile</h4>
          </div>
          <div class="card-body">
            <div v-if="user">
              <p><strong>Name:</strong> {{ user.username }}</p>
              <p><strong>Email:</strong> {{ user.email }}</p>
              <p><strong>Role:</strong> {{ user.role }}</p>
              <p v-if="user.full_name"><strong>Full Name:</strong> {{ user.full_name }}</p>
              <p><strong>Account Created:</strong> {{ new Date(user.created_at).toLocaleDateString() }}</p>
              <router-link to="/update-profile" class="btn btn-primary me-2">Update Profile</router-link>
              <button @click="confirmDeleteAccount" class="btn btn-danger">Delete Account</button>
            </div>
            <div v-else>
              <p>Loading user data...</p>
            </div>

            <div v-if="emailVerificationMessage" class="alert alert-info mt-3" role="alert">
                {{ emailVerificationMessage }}
            </div>
            <div v-if="errorMessage" class="alert alert-danger mt-3" role="alert">
                {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success mt-3" role="alert">
                {{ successMessage }}
            </div>
          </div>
        </div>

        <!-- My Farms & Personnel Section for Farmers -->
        <div class="card mb-4" v-if="user?.role === 'farmer'">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4>My Farms & Support Staff</h4>
            <router-link to="/middleman-access" class="btn btn-sm btn-outline-primary">Manage Personnel</router-link>
          </div>
          <div class="card-body">
            <div v-if="isFarmsLoading" class="text-center">
              <div class="spinner-border spinner-border-sm" role="status"></div>
            </div>
            <div v-else-if="farms.length === 0" class="text-muted">
              You haven't registered any farms yet.
            </div>
            <div v-else>
              <div v-for="farm in farms" :key="farm.id" class="mb-4 pb-3 border-bottom last-child-no-border">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <h5 class="mb-0">{{ farm.name }}</h5>
                  <span class="badge bg-info text-dark">{{ farm.device_ids?.length || 0 }} Device(s)</span>
                </div>
                
                <div class="ms-3 mt-2">
                  <h6 class="text-muted small mb-2">Primary Officer:</h6>
                  <div v-if="getOfficerForFarm(farm)" class="d-flex justify-content-between align-items-center bg-light p-2 rounded">
                    <div>
                      <span class="fw-bold">{{ getOfficerForFarm(farm).username }}</span>
                      <br>
                      <small class="text-muted">{{ getOfficerForFarm(farm).email }}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" @click="revokeAccess(getOfficerForFarm(farm))" :disabled="isRevoking">
                      Revoke Access
                    </button>
                  </div>
                  <div v-else class="text-muted small italic">No officer assigned to this farm.</div>
                </div>

                <div class="ms-3 mt-3">
                  <h6 class="text-muted small mb-2">Assigned Middlemen:</h6>
                  <div v-if="getMiddlemenForFarm(farm).length > 0" class="list-group list-group-flush">
                    <div v-for="m in getMiddlemenForFarm(farm)" :key="m.id" class="list-group-item d-flex justify-content-between align-items-center bg-transparent px-0 py-2">
                      <div>
                        <span>{{ m.username }}</span>
                        <small class="text-muted ms-2">({{ m.email }})</small>
                      </div>
                      <button class="btn btn-xs btn-link text-danger p-0" @click="revokeAccess(m)" :disabled="isRevoking">
                        Revoke Access
                      </button>
                    </div>
                  </div>
                  <div v-else class="text-muted small italic">No middlemen assigned to this farm.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Assigned Farmers Section for Middlemen/Officers -->
        <div class="card mb-4" v-if="user?.role === 'officer' || user?.role === 'middleman'">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4>Assigned Farmers</h4>
            <router-link to="/assigned-farms" class="btn btn-sm btn-outline-primary">View Assigned Farms</router-link>
          </div>
          <div class="card-body">
            <div v-if="isFarmersLoading" class="text-center">
              <div class="spinner-border spinner-border-sm" role="status"></div>
            </div>
            <div v-else-if="assignedFarmers.length === 0" class="text-muted">
              No farmers assigned to you yet.
            </div>
            <div v-else class="list-group">
              <div v-for="farmer in assignedFarmers" :key="farmer.id" class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-0">{{ farmer.username }}</h6>
                  <small class="text-muted">{{ farmer.email }}</small>
                </div>
                <router-link :to="{ name: 'Dashboard', query: { farmerId: farmer.id } }" class="btn btn-sm btn-outline-primary">
                  View Data
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <div class="card mb-4">
          <div class="card-header">
            <h4>Preferences</h4>
          </div>
          <div class="card-body">
            <form v-if="userPreferences" @submit.prevent="savePreferences">
              <div class="mb-3">
                <label for="temperatureUnit" class="form-label">Temperature Unit</label>
                <select id="temperatureUnit" class="form-select" v-model="userPreferences.temperature_unit">
                  <option value="Celsius">Celsius</option>
                  <option value="Fahrenheit">Fahrenheit</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="volumeUnit" class="form-label">Volume Unit</label>
                <select id="volumeUnit" class="form-select" v-model="userPreferences.volume_unit">
                  <option value="liters">Liters</option>
                  <option value="gallons">Gallons</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="timeZone" class="form-label">Time Zone</label>
                <input type="text" id="timeZone" class="form-control" v-model="userPreferences.time_zone">
              </div>
              <button type="submit" class="btn btn-success">Save Preferences</button>
            </form>
            <div v-else>
              <p>Loading preferences...</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h4>Notification Preferences</h4>
          </div>
          <div class="card-body">
            <form v-if="notificationPreferences" @submit.prevent="saveNotificationPreferences">
              <div class="mb-3">
                <label for="onCritical" class="form-label">Critical Alerts</label>
                <select id="onCritical" class="form-select" v-model="notificationPreferences.on_critical_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onHigh" class="form-label">High Alerts</label>
                <select id="onHigh" class="form-select" v-model="notificationPreferences.on_high_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onMedium" class="form-label">Medium Alerts</label>
                <select id="onMedium" class="form-select" v-model="notificationPreferences.on_medium_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="onLow" class="form-label">Low Alerts</label>
                <select id="onLow" class="form-select" v-model="notificationPreferences.on_low_alert">
                  <option value="email">Email</option>
                  <option value="in_app">In-App</option>
                  <option value="none">None</option>
                </select>
              </div>
              <button type="submit" class="btn btn-success">Save Notification Settings</button>
            </form>
            <div v-else>
              <p>Loading notification preferences...</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { authStore, fetchUser } from '@/store/auth';
import { authService } from '@/services/auth';
import { apiService } from '@/services/api';

const user = ref(null);
const userPreferences = ref(null);
const notificationPreferences = ref(null);
const assignedPersonnel = ref([]);
const assignedFarmers = ref([]);
const farms = ref([]);
const isPersonnelLoading = ref(false);
const isFarmersLoading = ref(false);
const isFarmsLoading = ref(false);
const isRevoking = ref(false);
const emailVerificationMessage = ref('');
const errorMessage = ref('');
const successMessage = ref('');

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  user.value = authStore.user;
  if (user.value) {
    try {
      userPreferences.value = await apiService.getUserPreferences(user.value.id);
      notificationPreferences.value = await apiService.getUserNotificationPreferences(user.value.id);
      
      if (user.value.role === 'farmer') {
        await loadPersonnel();
        await loadFarms();
      } else if (user.value.role === 'officer' || user.value.role === 'middleman') {
        await loadFarmers();
      }
    } catch (error) {
      console.error('Failed to load user settings:', error);
      errorMessage.value = 'Failed to load user settings.';
    }
  }
});

const loadPersonnel = async () => {
  isPersonnelLoading.value = true;
  try {
    assignedPersonnel.value = await apiService.getMiddlemanForFarmer(user.value.id);
  } catch (error) {
    console.error('Failed to load personnel:', error);
  } finally {
    isPersonnelLoading.value = false;
  }
};

const loadFarmers = async () => {
  isFarmersLoading.value = true;
  try {
    assignedFarmers.value = await apiService.getFarmersForMiddleman(user.value.id);
  } catch (error) {
    console.error('Failed to load farmers:', error);
  } finally {
    isFarmersLoading.value = false;
  }
};

const loadFarms = async () => {
  isFarmsLoading.value = true;
  try {
    farms.value = await apiService.getFarms();
  } catch (error) {
    console.error('Failed to load farms:', error);
  } finally {
    isFarmsLoading.value = false;
  }
};

const getOfficerForFarm = (farm) => {
  if (!farm.assigned_officer_id) return null;
  return assignedPersonnel.value.find(p => p.id === farm.assigned_officer_id);
};

const getMiddlemenForFarm = (farm) => {
  if (!farm.assigned_middleman_ids) return [];
  return assignedPersonnel.value.filter(p => 
    farm.assigned_middleman_ids.includes(p.id) && p.id !== farm.assigned_officer_id
  );
};

const revokeAccess = async (person) => {
  if (!confirm(`Revoke access for ${person.username}?`)) return;
  
  isRevoking.value = true;
  try {
    await apiService.revokeMiddlemanFromFarmer(user.value.id, person.id);
    // Refresh lists
    await loadPersonnel();
    await loadFarms();
    successMessage.value = 'Access revoked successfully.';
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error('Failed to revoke access:', error);
    errorMessage.value = 'Failed to revoke access.';
  } finally {
    isRevoking.value = false;
  }
};

const savePreferences = async () => {
  if (!user.value || !userPreferences.value) return;
  try {
    await apiService.updateUserPreferences(user.value.id, userPreferences.value);
    successMessage.value = 'Preferences saved successfully!';
    errorMessage.value = '';
    // Refresh user data to update preferences in the store
    await fetchUser();
    user.value = authStore.user;
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error('Failed to save preferences:', error);
    errorMessage.value = 'Failed to save preferences.';
    successMessage.value = '';
  }
};

const saveNotificationPreferences = async () => {
  if (!user.value || !notificationPreferences.value) return;
  try {
    await apiService.updateUserNotificationPreferences(user.value.id, notificationPreferences.value);
    successMessage.value = 'Notification preferences saved successfully!';
    errorMessage.value = '';
    // Refresh user data to update preferences in the store
    await fetchUser();
    user.value = authStore.user;
    setTimeout(() => successMessage.value = '', 3000);
  } catch (error) {
    console.error('Failed to save notification preferences:', error);
    errorMessage.value = 'Failed to save notification preferences.';
    successMessage.value = '';
  }
};

const confirmDeleteAccount = async () => {
  if (confirm('Are you sure you want to delete your account? This action requires email verification.')) {
    try {
      const result = await authService.sendDeleteAccountVerificationEmail();
      if (result.success) {
        emailVerificationMessage.value = 'A verification email has been sent. Please click the link in the email to confirm account deletion.';
        successMessage.value = '';
        errorMessage.value = '';
      } else {
        errorMessage.value = result.message;
      }
    } catch (error) {
      console.error('Error initiating delete account verification:', error);
      errorMessage.value = error.message || 'Failed to initiate account deletion verification.';
    }
  }
};
</script>

<style scoped>
.card {
  overflow: hidden; /* Ensures inner elements don't overflow rounded corners */
}

.list-group-item {
  border-left: none;
  border-right: none;
}

.list-group-item:first-child {
  border-top: none;
}

.list-group-item:last-child {
  border-bottom: none;
}

.last-child-no-border:last-child {
  border-bottom: none !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

.btn-xs {
  padding: 0.1rem 0.25rem;
  font-size: 0.75rem;
}

.italic {
  font-style: italic;
}
</style>
