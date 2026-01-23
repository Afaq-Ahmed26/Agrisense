<template>
  <div class="card shadow mb-4">
    <div class="card-header py-3">
      <h6 class="m-0 font-weight-bold text-primary">Predicted Water Requirements (Next 48 Hours)</h6>
    </div>
    <div class="card-body">
      <div class="chart-area">
        <canvas ref="chartCanvas"></canvas>
      </div>
      <div v-if="nextIrrigation" class="mt-2 text-center small">
        <strong>Next recommended irrigation:</strong>
        {{ nextIrrigation.time.toLocaleString() }}
        ({{ nextIrrigation.waterLiters }} L)
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue';
import { Chart, registerables } from 'chart.js';
import { apiService } from '@/services/api';
import { CHART_UPDATE_INTERVAL } from '@/config';

Chart.register(...registerables);

const deviceId = ref(localStorage.getItem('selectedDeviceId') || 'device_001');
const chartCanvas = ref(null);
const chartInstance = shallowRef(null);
const predictionData = ref([]);
const nextIrrigation = ref(null);
const timeRange = 48; // hours

let updateInterval = null;

onMounted(async () => {
  await loadPredictionData();
  renderChart();
  updateInterval = setInterval(async () => {
    await loadPredictionData();
    updateChart();
  }, CHART_UPDATE_INTERVAL);
});

onBeforeUnmount(() => {
  clearInterval(updateInterval);
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
});

const loadPredictionData = async () => {
  try {
    const response = await apiService.getIrrigationPredictions(deviceId.value, timeRange);
    predictionData.value = response.predictions || [];
    findNextIrrigation();
  } catch (error) {
    console.error('Error loading prediction data:', error);
    predictionData.value = generateDemoData(); // Fallback to demo data
    findNextIrrigation();
  }
};

const findNextIrrigation = () => {
    const next = predictionData.value.find(p => p.irrigation_needed);
    if (next) {
        nextIrrigation.value = {
            time: new Date(next.time),
            waterLiters: next.water_liters,
        };
    } else {
        nextIrrigation.value = null;
    }
}

const generateDemoData = () => {
    const data = [];
    const now = new Date();
    for (let i = 0; i < timeRange; i++) {
        data.push({
            time: new Date(now.getTime() + i * 60 * 60 * 1000).toISOString(),
            irrigation_needed: Math.random() > 0.7,
            water_liters: Math.floor(Math.random() * 50) + 20,
            confidence: Math.random() * 0.3 + 0.7
        });
    }
    return data;
};

const getChartData = () => {
  const data = predictionData.value;
  return {
    labels: data.map(p => new Date(p.time).toLocaleTimeString([], { hour: '2-digit' })),
    datasets: [{
      label: 'Water Needed (Liters)',
      data: data.map(p => p.irrigation_needed ? p.water_liters : null),
      backgroundColor: data.map(p => p.irrigation_needed ? 'rgba(54, 162, 235, 0.6)' : 'transparent'),
      borderColor: data.map(p => p.irrigation_needed ? 'rgba(54, 162, 235, 1)' : 'transparent'),
      borderWidth: 1,
      borderRadius: 4,
    }]
  };
};

const renderChart = () => {
  if (!chartCanvas.value) return;
  const ctx = chartCanvas.value.getContext('2d');
  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: getChartData(),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
            callbacks: {
                label: (context) => {
                    const item = predictionData.value[context.dataIndex];
                    if (item.irrigation_needed) {
                        return `Water: ${item.water_liters} L (Confidence: ${(item.confidence * 100).toFixed(0)}%)`;
                    }
                    return 'No irrigation predicted';
                }
            }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Water (Liters)' }
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
