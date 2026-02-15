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
        ({{ nextIrrigation.waterLiters }} {{ nextIrrigation.unit }})
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, shallowRef } from 'vue';
import { Chart, registerables } from 'chart.js';
import { formatWithUserPreferences } from '@/utils/unitConverter';
import { authStore } from '@/store/auth';

Chart.register(...registerables);

const chartCanvas = ref(null);
const chartInstance = shallowRef(null);
const predictionData = ref([]);
const nextIrrigation = ref(null);
const timeRange = 48; // hours

onMounted(() => {
  loadPredictionData();
  renderChart();
});

onBeforeUnmount(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy();
  }
});

const loadPredictionData = () => {
  predictionData.value = generateDemoData();
  findNextIrrigation();
};

const findNextIrrigation = () => {
    const next = predictionData.value.find(p => p.irrigation_needed);
    if (next) {
        // Convert water volume to user's preferred unit
        const userPrefs = authStore.user?.preferences || {
            temperature_unit: 'Celsius',
            volume_unit: 'liters',
            time_zone: 'UTC',
            notification_sound: 'default'
        };
        const convertedVolume = formatWithUserPreferences(next.water_liters, 'volume', userPrefs);
        nextIrrigation.value = {
            time: new Date(next.time),
            waterLiters: convertedVolume.value,
            unit: convertedVolume.unit
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
  // Convert all water volumes to user's preferred unit
  const userPrefs = authStore.user?.preferences || {
    temperature_unit: 'Celsius',
    volume_unit: 'liters',
    time_zone: 'UTC',
    notification_sound: 'default'
  };
  const convertedData = data.map(item => {
    if (item.irrigation_needed) {
      const converted = formatWithUserPreferences(item.water_liters, 'volume', userPrefs);
      return { ...item, water_liters_converted: converted.value };
    }
    return { ...item, water_liters_converted: null };
  });
  
  const volumeUnit = formatWithUserPreferences(0, 'volume', userPrefs).unit;
  
  return {
    labels: convertedData.map(p => new Date(p.time).toLocaleTimeString([], { hour: '2-digit' })),
    datasets: [{
      label: `Water Needed (${volumeUnit})`,
      data: convertedData.map(p => p.irrigation_needed ? p.water_liters_converted : null),
      backgroundColor: convertedData.map(p => p.irrigation_needed ? 'rgba(54, 162, 235, 0.6)' : 'transparent'),
      borderColor: convertedData.map(p => p.irrigation_needed ? 'rgba(54, 162, 235, 1)' : 'transparent'),
      borderWidth: 1,
      borderRadius: 4,
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
                        // Convert the water volume to user's preferred unit
                        const converted = formatWithUserPreferences(item.water_liters, 'volume', userPrefs);
                        return `Water: ${converted.formatted} (Confidence: ${(item.confidence * 100).toFixed(0)}%)`;
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
          title: { display: true, text: `Water (${formatWithUserPreferences(0, 'volume', userPrefs).unit})` }
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
    chartInstance.value.options.scales.y.title.text = `Water (${formatWithUserPreferences(0, 'volume', authStore.user?.preferences || {}).unit})`;
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
