<template>
  <div class="connect-device-view">
    <h2>Connect a New Device</h2>
    <form @submit.prevent="connectDevice">
      <div class="form-group">
        <label for="deviceId">Device ID</label>
        <input type="text" id="deviceId" v-model="device.id" required>
      </div>
      <div class="form-group">
        <label for="deviceType">Device Type</label>
        <input type="text" id="deviceType" v-model="device.type" required>
      </div>
      <div class="form-group">
        <label for="deviceLocation">Device Location</label>
        <input type="text" id="deviceLocation" v-model="device.location" required>
      </div>
      <button type="submit">Connect</button>
    </form>
    <div v.if="device.id" class="device-status">
      <h3>Device Status</h3>
      <p><strong>ID:</strong> {{ device.id }}</p>
      <p><strong>Type:</strong> {{ device.type }}</p>
      <p><strong>Location:</strong> {{ device.location }}</p>
      <p><strong>Status:</strong> <span class="offline">Offline (Simulated)</span></p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ConnectDeviceView',
  data() {
    return {
      device: {
        id: '',
        type: '',
        location: '',
      },
    };
  },
  methods: {
    connectDevice() {
      // For now, this is just a placeholder.
      // In the future, this would involve actual device registration logic.
      console.log('Connecting device:', this.device);
    },
  },
};
</script>

<style scoped>
.connect-device-view {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
}

input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  padding: 0.75rem 1.5rem;
  background-color: #4080FF;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #3366CC;
}

.device-status {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.offline {
  color: #FF4136;
}
</style>
