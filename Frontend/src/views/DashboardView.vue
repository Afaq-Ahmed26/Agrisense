<template>
  <div>
    <AlertsBanner />
    <div class="container-fluid px-4 mt-3">
      <div class="d-flex justify-content-end mb-3">
        <button class="btn btn-info me-2" @click="$router.push({ name: 'ConnectDevice' })">
          Connect New Device
        </button>
        <button class="btn btn-secondary" @click="toggleCustomizeMode">
          {{ customizeMode ? 'Finish Customizing' : 'Customize Dashboard' }}
        </button>
        <button v-if="customizeMode" class="btn btn-primary ms-2" @click="saveLayout">
          Save Layout
        </button>
      </div>

      <div class="row">
        <div class="col-lg-12" v-for="widget in dashboardLayout" :key="widget.id" v-show="widget.visible">
          <div class="position-relative">
            <component :is="getComponent(widget.id)"></component>
            <button v-if="customizeMode" class="btn btn-danger btn-sm position-absolute top-0 end-0" @click="hideWidget(widget)">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <div v-if="customizeMode && hiddenWidgets.length > 0" class="mt-4">
        <h5>Hidden Widgets</h5>
        <ul class="list-group">
          <li v-for="widget in hiddenWidgets" :key="widget.id" class="list-group-item d-flex justify-content-between align-items-center">
            {{ widget.id }}
            <button class="btn btn-success btn-sm" @click="showWidget(widget)">
              <i class="fas fa-plus"></i>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { VueDraggableNext as draggable } from 'vue-draggable-next';
import AlertsBanner from '@/components/AlertsBanner.vue';
import SensorDisplay from '@/components/SensorDisplay.vue';
import IrrigationControl from '@/components/IrrigationControl.vue';
import PredictionChart from '@/components/PredictionChart.vue';
import LogsTable from '@/components/LogsTable.vue';
import { authStore, fetchUser } from '@/store/auth';
import { apiService } from '@/services/api';

const customizeMode = ref(false);
const dashboardLayout = ref([]);

const availableWidgets = {
  AlertsBanner: AlertsBanner,
  SensorDisplay: SensorDisplay,
  IrrigationControl: IrrigationControl,
  PredictionChart: PredictionChart,
  LogsTable: LogsTable
};

const defaultLayout = [
  { id: 'AlertsBanner', component: 'AlertsBanner', visible: true, order: 1 },
  { id: 'SensorDisplay', component: 'SensorDisplay', visible: true, order: 2 },
  { id: 'IrrigationControl', component: 'IrrigationControl', visible: true, order: 3 },
  { id: 'PredictionChart', component: 'PredictionChart', visible: true, order: 4 },
  { id: 'LogsTable', component: 'LogsTable', visible: true, order: 5 }
];

onMounted(async () => {
  if (!authStore.user) {
    await fetchUser();
  }
  if (authStore.user && authStore.user.dashboard_preferences) {
    dashboardLayout.value = authStore.user.dashboard_preferences;
  } else {
    dashboardLayout.value = defaultLayout;
  }
});

const getComponent = (componentName) => {
  const component = availableWidgets[componentName];
  return component;
};

const toggleCustomizeMode = () => {
  customizeMode.value = !customizeMode.value;
};

const hideWidget = (widget) => {
  widget.visible = false;
};

const showWidget = (widget) => {
  widget.visible = true;
};

const hiddenWidgets = computed(() => {
  return dashboardLayout.value.filter(widget => !widget.visible);
});

const saveLayout = async () => {
  try {
    await apiService.updateUser(authStore.user.id, { dashboard_preferences: dashboardLayout.value });
    await fetchUser(); // Re-fetch user to update local store
    customizeMode.value = false;
    // Optionally, show a success message
  } catch (error) {
    console.error('Failed to save dashboard layout:', error);
    // Optionally, show an error message
  }
};
</script>

<style scoped>
.position-relative {
  padding-top: 2.5rem; /* Add padding to prevent overlap with the remove button */
}
</style>
