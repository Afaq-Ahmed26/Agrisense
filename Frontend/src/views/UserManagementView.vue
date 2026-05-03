<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <!-- Tab Navigation -->
        <ul class="nav nav-tabs mb-4" role="tablist">
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link active" 
              :class="{ active: activeTab === 'users' }"
              @click="activeTab = 'users'"
              type="button">
              Active Users
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'middleman' }"
              @click="activeTab = 'middleman'"
              type="button">
              Middleman Assignment
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button 
              class="nav-link" 
              :class="{ active: activeTab === 'deleted' }"
              @click="activeTab = 'deleted'"
              type="button">
              Deleted Users
            </button>
          </li>
        </ul>

        <!-- Active Users Tab -->
        <div v-if="activeTab === 'users'" class="card">
          <div class="card-header">
            <h4>User Management</h4>
          </div>
          <div class="card-body">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Assigned Device IDs</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.username }}</td>
                  <td>{{ user.email }}</td>
                  <td>
                    <div class="d-flex align-items-center">
                      <select class="form-select" 
                              :value="user.role" 
                              @change="updateUserRole(user, $event.target.value)"
                              :disabled="user.isUpdatingRole || user.id === authStore.user?.id">
                        <option value="farmer">Farmer</option>
                        <option value="officer">Officer</option>
                        <option v-if="isAdmin" value="admin">Admin</option>
                      </select>
                      <div v-if="user.isUpdatingRole" class="spinner-border spinner-border-sm text-primary ms-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <div class="d-flex align-items-center">
                      <input
                        type="text"
                        class="form-control form-control-sm"
                        v-model="user.assignedDevicesInput"
                        placeholder="esp32-b47cb8, esp32-xyz"
                        :disabled="!canEditAssignments(user) || user.isUpdatingAssignments"
                      />
                      <button
                        class="btn btn-sm btn-outline-primary ms-2"
                        @click="updateAssignedDevices(user)"
                        :disabled="!canEditAssignments(user) || user.isUpdatingAssignments"
                      >
                        <span v-if="user.isUpdatingAssignments" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        <span v-else>Save</span>
                      </button>
                    </div>
                  </td>
                  <td>
                    <div class="d-flex align-items-center gap-3">
                      <span :class="['badge', user.is_active ? 'bg-success' : 'bg-danger']" style="min-width: 70px;">
                        {{ user.is_active ? 'Active' : 'Inactive' }}
                      </span>
                      <div class="btn-group">
                        <button class="btn btn-sm btn-primary" 
                                @click="toggleUserStatus(user)"
                                :disabled="user.id === authStore.user?.id">
                          {{ user.is_active ? 'Deactivate' : 'Activate' }}
                        </button>
                        <button class="btn btn-sm btn-danger" 
                                @click="deleteUserPrompt(user)"
                                :disabled="user.id === authStore.user?.id">
                          Delete
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Middleman Assignment Tab -->
        <div v-if="activeTab === 'middleman'" class="card">
          <div class="card-header">
            <h4>Assign Middlemen to Farmers</h4>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label for="farmerSelect" class="form-label">Select Farmer:</label>
              <select v-model="selectedFarmerId" class="form-select" id="farmerSelect">
                <option value="">-- Choose a farmer --</option>
                <option v-for="farmer in farmers" :key="farmer.id" :value="farmer.id">
                  {{ farmer.username }} ({{ farmer.email }})
                </option>
              </select>
            </div>

            <div v-if="selectedFarmerId" class="mb-3">
              <label for="middlemanSelect" class="form-label">Assign Middlemen:</label>
              <div class="mb-2">
                <select v-model="selectedMiddlemanId" class="form-select" id="middlemanSelect">
                  <option value="">-- Choose middleman/officer --</option>
                  <option v-for="officer in officers" :key="officer.id" :value="officer.id">
                    {{ officer.username }} ({{ officer.email }})
                  </option>
                </select>
              </div>
              <button 
                class="btn btn-outline-primary"
                @click="assignMiddleman"
                :disabled="!selectedMiddlemanId || isAssigningMiddleman">
                <span v-if="isAssigningMiddleman" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Assign Middleman
              </button>
            </div>

            <!-- Currently assigned middlemen -->
            <div v-if="selectedFarmerId" class="mt-4">
              <h5>Assigned Middlemen:</h5>
              <div v-if="currentFarmerMiddlemen.length > 0" class="list-group">
                <div v-for="middleman in currentFarmerMiddlemen" :key="middleman.id" class="list-group-item d-flex justify-content-between align-items-center">
                  <div>
                    <strong>{{ middleman.username }}</strong><br>
                    <small class="text-muted">{{ middleman.email }}</small>
                  </div>
                  <button 
                    class="btn btn-sm btn-danger"
                    @click="revokeMiddleman(middleman.id)"
                    :disabled="isRevokingMiddleman">
                    <span v-if="isRevokingMiddleman" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                    Revoke
                  </button>
                </div>
              </div>
              <p v-else class="text-muted mt-2">No middlemen assigned to this farmer yet.</p>
            </div>
          </div>
        </div>

        <!-- Deleted Users Tab -->
        <div v-if="activeTab === 'deleted'" class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h4>Deleted Users (7-Day Recovery)</h4>
            <button 
              class="btn btn-sm btn-outline-secondary"
              @click="refreshDeletedUsers"
              :disabled="isLoadingDeleted">
              Refresh
            </button>
          </div>
          <div class="card-body">
            <div v-if="isLoadingDeleted" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
            <div v-else-if="deletedUsers.length === 0" class="alert alert-info">
              No deleted users in the system.
            </div>
            <div v-else class="table-responsive">
              <table class="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Deleted On</th>
                    <th>Recovery Deadline</th>
                    <th>Days Left</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in deletedUsers" :key="user.id">
                    <td>{{ user.username }}</td>
                    <td>{{ user.email }}</td>
                    <td>{{ user.role }}</td>
                    <td>{{ formatDate(user.deleted_at) }}</td>
                    <td>{{ formatDate(user.recovery_deadline) }}</td>
                    <td>
                      <span v-if="user.is_recoverable" class="badge bg-warning">
                        {{ user.days_until_expiry }} days
                      </span>
                      <span v-else class="badge bg-danger">Expired</span>
                    </td>
                    <td>
                      <button 
                        v-if="user.is_recoverable"
                        class="btn btn-sm btn-success"
                        @click="restoreUser(user.id)"
                        :disabled="isRestoringUser">
                        <span v-if="isRestoringUser" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                        Restore
                      </button>
                      <button 
                        v-else
                        class="btn btn-sm btn-secondary"
                        disabled>
                        Expired
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirm" class="modal d-block" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Deletion</h5>
            <button type="button" class="btn-close" @click="showDeleteConfirm = false"></button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to delete <strong>{{ userToDelete?.username }}</strong>?
            </p>
            <p class="text-muted small">
              The user can be recovered within 7 days. After that, the account will be permanently deleted.
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDeleteConfirm = false">Cancel</button>
            <button 
              type="button" 
              class="btn btn-danger"
              @click="confirmDeleteUser"
              :disabled="isDeletingUser">
              <span v-if="isDeletingUser" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Delete User
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { apiService } from '@/services/api';
import { authStore } from '@/store/auth';

const users = ref([]);
const deletedUsers = ref([]);
const farmers = ref([]);
const officers = ref([]);
const activeTab = ref('users');
const isAdmin = computed(() => authStore.user?.role === 'admin');

// Middleman management state
const selectedFarmerId = ref('');
const selectedMiddlemanId = ref('');
const currentFarmerMiddlemen = ref([]);
const isAssigningMiddleman = ref(false);
const isRevokingMiddleman = ref(false);

// Deleted users management state
const isLoadingDeleted = ref(false);
const isRestoringUser = ref(false);

// Delete confirmation state
const showDeleteConfirm = ref(false);
const userToDelete = ref(null);
const isDeletingUser = ref(false);

const refreshUserLists = async () => {
  try {
    const fetchedUsers = await apiService.getUsers();
    users.value = fetchedUsers.map(user => ({
      ...user,
      isUpdatingRole: false,
      isUpdatingAssignments: false,
      assignedDevicesInput: (user.assigned_device_ids || []).join(', ')
    }));

    // Separate farmers and officers
    farmers.value = fetchedUsers.filter(u => u.role === 'farmer');
    officers.value = fetchedUsers.filter(u => u.role === 'officer' || u.role === 'middleman');
  } catch (error) {
    console.error('Failed to refresh user lists:', error);
  }
};

onMounted(async () => {
  await refreshUserLists();
});

const isOfficer = (user) => {
  const role = (user.role || '').toLowerCase();
  return role === 'officer' || role === 'middleman';
};

const isFarmer = (user) => (user.role || '').toLowerCase() === 'farmer';

const canEditAssignments = (user) => isAdmin.value && (isOfficer(user) || isFarmer(user));

const toggleUserStatus = async (user) => {
  try {
    await apiService.updateUser(user.id, { is_active: !user.is_active });
    await refreshUserLists();
  } catch (error) {
    console.error(`Failed to toggle user status for user ${user.id}:`, error);
    alert('Failed to update user status');
  }
};

const updateUserRole = async (user, newRole) => {
  const originalRole = user.role;
  user.isUpdatingRole = true;
  try {
    await apiService.updateUser(user.id, { role: newRole });
    await refreshUserLists();
  } catch (error) {
    console.error(`Failed to change role for user ${user.id}:`, error);
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index].role = originalRole;
    }
    alert('Failed to update user role');
  } finally {
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index].isUpdatingRole = false;
    }
  }
};

const updateAssignedDevices = async (user) => {
  const index = users.value.findIndex(u => u.id === user.id);
  if (index === -1) return;

  users.value[index].isUpdatingAssignments = true;

  const assignedDeviceIds = (users.value[index].assignedDevicesInput || '')
    .split(',')
    .map(deviceId => deviceId.trim())
    .filter(Boolean);

  try {
    const updatedUser = await apiService.updateUser(user.id, {
      assigned_device_ids: assignedDeviceIds
    });

    users.value[index] = {
      ...updatedUser,
      isUpdatingRole: false,
      isUpdatingAssignments: false,
      assignedDevicesInput: (updatedUser.assigned_device_ids || []).join(', ')
    };
    alert('Device assignment updated successfully');
  } catch (error) {
    console.error(`Failed to update assigned devices for user ${user.id}:`, error);
    alert('Failed to update device assignment');
  } finally {
    const currentIndex = users.value.findIndex(u => u.id === user.id);
    if (currentIndex !== -1) {
      users.value[currentIndex].isUpdatingAssignments = false;
    }
  }
};

// Middleman management functions
const assignMiddleman = async () => {
  if (!selectedFarmerId.value || !selectedMiddlemanId.value) {
    alert('Please select both a farmer and a middleman');
    return;
  }

  isAssigningMiddleman.value = true;
  try {
    await apiService.assignMiddlemanToFarmer(selectedFarmerId.value, selectedMiddlemanId.value);
    loadFarmerMiddlemen();
    selectedMiddlemanId.value = '';
    alert('Middleman assigned successfully');
  } catch (error) {
    console.error('Failed to assign middleman:', error);
    alert('Failed to assign middleman');
  } finally {
    isAssigningMiddleman.value = false;
  }
};

const loadFarmerMiddlemen = async () => {
  try {
    const middlemen = await apiService.getMiddlemanForFarmer(selectedFarmerId.value);
    currentFarmerMiddlemen.value = middlemen;
  } catch (error) {
    console.error('Failed to load farmer middlemen:', error);
    currentFarmerMiddlemen.value = [];
  }
};

const revokeMiddleman = async (middlemanId) => {
  if (!window.confirm('Are you sure you want to revoke this middleman access?')) {
    return;
  }

  isRevokingMiddleman.value = true;
  try {
    await apiService.revokeMiddlemanFromFarmer(selectedFarmerId.value, middlemanId);
    loadFarmerMiddlemen();
    alert('Middleman access revoked');
  } catch (error) {
    console.error('Failed to revoke middleman:', error);
    alert('Failed to revoke middleman access');
  } finally {
    isRevokingMiddleman.value = false;
  }
};

// Watch for farmer selection change
watch(selectedFarmerId, () => {
  if (selectedFarmerId.value) {
    loadFarmerMiddlemen();
  } else {
    currentFarmerMiddlemen.value = [];
  }
});

// Deleted users management functions
const refreshDeletedUsers = async () => {
  isLoadingDeleted.value = true;
  try {
    deletedUsers.value = await apiService.getDeletedUsers();
  } catch (error) {
    console.error('Failed to fetch deleted users:', error);
    // Don't alert on CORS or transient errors to keep it clean
  } finally {
    isLoadingDeleted.value = false;
  }
};

const restoreUser = async (userId) => {
  if (!window.confirm('Restore this user?')) {
    return;
  }

  isRestoringUser.value = true;
  try {
    await apiService.restoreDeletedUser(userId);
    deletedUsers.value = deletedUsers.value.filter(u => u.id !== userId);
    // Reload active users and dropdowns
    await refreshUserLists();
    alert('User restored successfully');
  } catch (error) {
    console.error('Failed to restore user:', error);
    alert('Failed to restore user');
  } finally {
    isRestoringUser.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Delete user functions
const deleteUserPrompt = (user) => {
  userToDelete.value = user;
  showDeleteConfirm.value = true;
};

const confirmDeleteUser = async () => {
  if (!userToDelete.value) return;

  isDeletingUser.value = true;
  try {
    await apiService.deleteUser(userToDelete.value.id);
    users.value = users.value.filter(u => u.id !== userToDelete.value.id);
    showDeleteConfirm.value = false;
    userToDelete.value = null;
    alert('User deleted successfully (7-day recovery window enabled)');
    // Refresh deleted list if we are on that tab (implicitly handled by refresh if user switches)
  } catch (error) {
    console.error('Failed to delete user:', error);
    alert('Failed to delete user');
  } finally {
    isDeletingUser.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for UserManagementView */
</style>
