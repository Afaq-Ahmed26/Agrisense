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
                              :disabled="user.isUpdatingRole">
                        <option value="farmer">Farmer</option>
                        <option value="officer">Officer</option>
                        <!-- Admin role is not an option to prevent accidental changes -->
                      </select>
                      <div v-if="user.isUpdatingRole" class="spinner-border spinner-border-sm text-primary ms-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span :class="['badge', user.is_active ? 'bg-success' : 'bg-danger']">
                      {{ user.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-primary me-2" @click="toggleUserStatus(user)">
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
import { ref, onMounted } from 'vue';
import { apiService } from '@/services/api';

const users = ref([]);

onMounted(async () => {
  try {
    const fetchedUsers = await apiService.getUsers();
    users.value = fetchedUsers.map(user => ({ ...user, isUpdatingRole: false }));
  } catch (error) {
    console.error('Failed to fetch users:', error);
  }
});

const toggleUserStatus = async (user) => {
  try {
    const updatedUser = await apiService.updateUser(user.id, { is_active: !user.is_active });
    const index = users.value.findIndex(u => u.id === user.id);
    if (index !== -1) {
      users.value[index] = updatedUser;
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
      // Keep the isUpdatingRole property
      users.value[index] = { ...updatedUser, isUpdatingRole: false };
    }
  } catch (error) {
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
</script>

<style scoped>
/* Scoped styles for UserManagementView */
</style>
