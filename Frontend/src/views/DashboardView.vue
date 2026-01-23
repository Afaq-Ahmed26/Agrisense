<template>
  <div>
    <AlertsBanner />
    <div class="container-fluid px-4 mt-3">
      <div class="row">
        <div class="col-lg-12">
          <SensorDisplay ref="sensorDisplay" />
          <div class="row">
            <div class="col-lg-6">
              <IrrigationControl />
            </div>
            <div class="col-lg-6">
              <PredictionChart />
            </div>
          </div>
          <LogsTable />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import AlertsBanner from '@/components/AlertsBanner.vue';
import SensorDisplay from '@/components/SensorDisplay.vue';
import IrrigationControl from '@/components/IrrigationControl.vue';
import PredictionChart from '@/components/PredictionChart.vue';
import LogsTable from '@/components/LogsTable.vue';

const sensorDisplay = ref(null);

// In a real app, you might have a global state management or event bus
// to communicate between components, for example, to pass alerts from
// sensorDisplay to alertsBanner.
// For now, we are keeping it simple.

</script>

<style scoped>
/* Scoped styles for DashboardView */
</style>
