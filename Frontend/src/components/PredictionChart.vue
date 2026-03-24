<template>
  <div class="card shadow mb-4">
    <div class="card-header py-3">
      <h6 class="m-0 font-weight-bold text-primary">Current Irrigation Prediction</h6>
    </div>
    <div class="card-body">
      <div class="chart-area">
        <canvas ref="chartCanvas"></canvas>
      </div>
      <div v-if="nextIrrigation" class="mt-2 text-center small">
        <strong>Next recommended irrigation:</strong>
        {{ nextIrrigation.time.toLocaleString() }}
        ({{ nextIrrigation.waterLiters }} {{ nextIrrigation.unit }})
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, shallowRef, watch } from 'vue';
import { Chart, registerables } from 'chart.js';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';
import { apiService } from '@/services/api'; // Import apiService

Chart.register(...registerables);

const chartCanvas = ref(null);
const chartInstance = shallowRef(null);
const predictionData = ref(null); // Changed to null for single prediction
const timeRange = 48; // hours (still relevant for display context, but data will be single point for now)

const props = defineProps({
  deviceId: {
    type: String,
    required: true
  }
});

onMounted(() => {
  if (props.deviceId) {
    loadPredictionData(props.deviceId);
  }
  renderChart();
});

// Watch for deviceId changes
watch(() => props.deviceId, (newDeviceId) => {
  if (newDeviceId) {
    loadPredictionData(newDeviceId);
  } else {
    predictionData.value = null; // Clear prediction if no device
    updateChart();
  }
});

onBeforeUnmount(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
});

const loadPredictionData = async (deviceId) => {
  if (!deviceId) {
    predictionData.value = null;
    updateChart();
    return;
  }
  try {
    // Call the new API to get future irrigation predictions
    // Pass hoursAhead from timeRange
    const futurePredictions = await apiService.getIrrigationPredictions(deviceId, timeRange);
    
    if (futurePredictions && futurePredictions.length > 0) {
      // Store the list of predictions
      predictionData.value = futurePredictions;
    } else {
      console.warn(`No future predictions found for device ${deviceId}.`);
      predictionData.value = null;
    }
    updateChart(); // Update chart after new data is fetched
  } catch (error) {
    console.error('Failed to load future prediction data:', error);
    predictionData.value = null;
    updateChart();
  }
};

const getChartData = () => {
  const predictions = predictionData.value;
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  
  const volumeUnit = formatWithUserPreferences(0, 'volume', userPrefs).unit;

  if (!predictions || predictions.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: `Valve Duration (${volumeUnit})`,
        data: [],
        backgroundColor: 'rgba(200, 200, 200, 0.6)',
        borderColor: 'rgba(200, 200, 200, 1)',
        borderWidth: 1,
      }]
    };
  }

  // Generate labels for each hour, including date
  const labels = predictions.map(p => {
    const date = new Date(p.predicted_at);
    // Format to a readable date and time, e.g., "Feb 19, 6:00 PM"
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  });

  // Extract predicted valve durations
  const data = predictions.map(p => p.predicted_valve_duration_s / 60);

  return {
    labels: labels,
    datasets: [{
      label: `Valve Duration (${volumeUnit})`,
      data: data,
      backgroundColor: 'rgba(54, 162, 235, 0.6)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1,
      fill: false, // For line chart
      tension: 0.1 // For smooth lines
    }]
  };
};

const renderChart = () => {
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext('2d');
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  chartInstance.value = new Chart(ctx, {
    type: 'line', // Changed to line chart type for future predictions
    data: getChartData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                title: (tooltipItems) => {
                    return `Time: ${tooltipItems[0].label}`; // Show time in title
                },
                label: (context) => {
                    const duration = context.parsed.y;
                    if (duration > 0) {
                        return `Predicted Duration: ${duration.toFixed(1)} minutes`;
                    }
                    return 'No irrigation predicted';
                }
            }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          title: { display: true, text: 'Time Ahead' }, // X-axis title for time
          ticks: { maxRotation: 45, autoSkip: true } // Rotate labels for better readability
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Valve Duration (minutes)' }
        }
      }
    }
  });
};

const updateChart = () => {
  if (chartInstance.value) {
    const newChartData = getChartData();
    chartInstance.value.data.labels = newChartData.labels;
    chartInstance.value.data.datasets[0].data = newChartData.datasets[0].data;
    chartInstance.value.data.datasets[0].backgroundColor = newChartData.datasets[0].backgroundColor;
    chartInstance.value.data.datasets[0].borderColor = newChartData.datasets[0].borderColor;
    chartInstance.value.options.scales.y.title.text = 'Valve Duration (minutes)';
    
    // Update chart type if it somehow changed (though it shouldn't if set once)
    if (chartInstance.value.config.type !== 'line') {
      chartInstance.value.config.type = 'line';
    }
    
    chartInstance.value.update();
  }
};
</script>

<style scoped>
.chart-area {
  position: relative;
  height: 320px;
}
</style>
