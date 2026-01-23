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
                  <td>{{ user.role }}</td>
                  <td>
                    <span :class="['badge', user.is_active ? 'bg-success' : 'bg-danger']">
                      {{ user.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-primary me-2" @click="toggleUserStatus(user)">
                      {{ user.is_active ? 'Deactivate' : 'Activate' }}
                    </button>
                    <button class="btn btn-sm btn-secondary" @click="changeUserRole(user)">
                      Change Role
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
    users.value = await apiService.getUsers();
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

const changeUserRole = async (user) => {
  // This is a placeholder for a more complex implementation,
  // such as opening a modal with a role selector.
  const newRole = prompt(`Enter new role for ${user.username}: (farmer, admin, officer)`);
  if (newRole && ['farmer', 'admin', 'officer'].includes(newRole)) {
    try {
      const updatedUser = await apiService.updateUser(user.id, { role: newRole });
      const index = users.value.findIndex(u => u.id === user.id);
      if (index !== -1) {
        users.value[index] = updatedUser;
      }
    } catch (error) {
      console.error(`Failed to change role for user ${user.id}:`, error);
    }
  }
};
</script>

<style scoped>
/* Scoped styles for UserManagementView */
</style>
