<template>
  <div class="container mt-5">
    <div class="row">
      <div class="col">
        <div class="card">
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
                  <th>Status</th>
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
                    <span :class="['badge', user.is_active ? 'bg-success' : 'bg-danger']">
                      {{ user.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-primary me-2" 
                            @click="toggleUserStatus(user)"
                            :disabled="user.id === authStore.user?.id">
                      {{ user.is_active ? 'Deactivate' : 'Activate' }}
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
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiService } from '@/services/api';
import { authStore } from '@/store/auth';

const users = ref([]);

const isAdmin = computed(() => authStore.user?.role === 'admin');

onMounted(async () => {
  try {
    const fetchedUsers = await apiService.getUsers();
    users.value = fetchedUsers.map(user => ({
      ...user,
      isUpdatingRole: false,
      isUpdatingAssignments: false,
      assignedDevicesInput: (user.assigned_device_ids || []).join(', ')
    }));
  } catch (error) {
    console.error('Failed to fetch users:', error);
  }
});

const isOfficer = (user) => {
  const role = (user.role || '').toLowerCase();
  return role === 'officer' || role === 'middleman';
};

const isFarmer = (user) => (user.role || '').toLowerCase() === 'farmer';

const canEditAssignments = (user) => isAdmin.value && (isOfficer(user) || isFarmer(user));

const toggleUserStatus = async (user) => {
  try {
    const updatedUser = await apiService.updateUser(user.id, { is_active: !user.is_active });
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index] = {
        ...updatedUser,
        isUpdatingRole: false,
        isUpdatingAssignments: false,
        assignedDevicesInput: (updatedUser.assigned_device_ids || []).join(', ')
      };
    }
  } catch (error) {
    console.error(`Failed to toggle user status for user ${user.id}:`, error);
  }
};

const updateUserRole = async (user, newRole) => {
  const originalRole = user.role;
  user.isUpdatingRole = true;
  try {
    const updatedUser = await apiService.updateUser(user.id, { role: newRole });
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index] = {
        ...updatedUser,
        isUpdatingRole: false,
        isUpdatingAssignments: false,
        assignedDevicesInput: (updatedUser.assigned_device_ids || []).join(', ')
      };
    }
  } catch (error)
	{
    console.error(`Failed to change role for user ${user.id}:`, error);
    // Revert the change in the UI on error
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index].role = originalRole;
    }
  } finally {
    // Ensure the spinner is turned off
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
  } catch (error) {
    console.error(`Failed to update assigned devices for user ${user.id}:`, error);
  } finally {
    const currentIndex = users.value.findIndex(u => u.id === user.id);
    if (currentIndex !== -1) {
      users.value[currentIndex].isUpdatingAssignments = false;
    }
  }
};
</script>

<style scoped>
/* Scoped styles for UserManagementView */
</style>
