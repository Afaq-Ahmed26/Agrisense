<template>
  <div v-if="isOfficer" class="farmer-switcher card shadow mb-4">
    <div class="card-body py-2 d-flex align-items-center">
      <label class="me-3 mb-0 font-weight-bold">Assisting Farmer:</label>
      <select 
        class="form-select w-auto" 
        :value="officerStore.selectedFarmerId" 
        @change="onFarmerChange"
      >
        <option :value="null">All Farms (Global View)</option>
        <option 
          v-for="farmer in officerStore.managedFarmers" 
          :key="farmer.id" 
          :value="farmer.id"
        >
          {{ farmer.full_name || farmer.username }} ({{ farmer.email }})
        </option>
      </select>
      <div v-if="loading" class="ms-3 spinner-border spinner-border-sm text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { authStore } from '@/store/auth';
import { officerStore, setSelectedFarmerId, setManagedFarmers } from '@/store/officer';
import { apiService } from '@/services/api';

const loading = ref(false);

const isOfficer = computed(() => {
  const role = (authStore.user?.role || '').toLowerCase();
  return role === 'officer' || role === 'middleman';
});

const onFarmerChange = (event) => {
  const value = event.target.value === 'null' ? null : event.target.value;
  setSelectedFarmerId(value);
};

onMounted(async () => {
  if (isOfficer.value && officerStore.managedFarmers.length === 0) {
    loading.value = true;
    try {
      const farmers = await apiService.getManagedFarmers();
      setManagedFarmers(Array.isArray(farmers) ? farmers : []);
    } catch (error) {
      console.error('Failed to load managed farmers:', error);
    } finally {
      loading.value = false;
    }
  }
});
</script>

<style scoped>
.farmer-switcher {
  border-left: 0.25rem solid #4e73df;
}
</style>
