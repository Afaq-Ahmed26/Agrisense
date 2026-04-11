<template>
  <div v-if="isVisible" class="custom-modal-overlay">
    <div class="custom-modal card shadow-lg animate__animated animate__zoomIn">
      <div class="card-header border-0 bg-transparent text-center pt-4">
        <div class="icon-circle mb-3" :class="typeClass">
          <i :class="iconClass"></i>
        </div>
        <h4 class="card-title font-weight-bold">{{ title }}</h4>
      </div>
      <div class="card-body text-center pb-4">
        <p class="text-muted">{{ message }}</p>
        <button class="btn btn-primary px-5 rounded-pill mt-3" @click="close">
          Dismiss
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const isVisible = ref(false);
const message = ref('');
const title = ref('');
const type = ref('info'); // 'info', 'success', 'error'

const show = (msg, t = 'Info', tp = 'info') => {
  message.value = msg;
  title.value = t;
  type.value = tp;
  isVisible.value = true;
};

const close = () => {
  isVisible.value = false;
};

const typeClass = computed(() => {
  return {
    'bg-success-light': type.value === 'success',
    'bg-danger-light': type.value === 'error',
    'bg-primary-light': type.value === 'info'
  };
});

const iconClass = computed(() => {
  return {
    'fas fa-check text-success': type.value === 'success',
    'fas fa-times text-danger': type.value === 'error',
    'fas fa-info text-primary': type.value === 'info'
  };
});

defineExpose({ show });
</script>

<style scoped>
.custom-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.custom-modal {
  width: 90%;
  max-width: 400px;
  border-radius: 20px;
  border: none;
}

.icon-circle {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
  font-size: 30px;
}

.bg-success-light { background-color: #e6f7ee; }
.bg-danger-light { background-color: #fbeaea; }
.bg-primary-light { background-color: #e8f0fe; }

.animate__animated {
  animation-duration: 0.3s;
}

@keyframes zoomIn {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.animate__zoomIn {
  animation-name: zoomIn;
}
</style>
