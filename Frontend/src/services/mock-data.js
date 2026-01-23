// Mock data service for AgriSense frontend
// This provides sample data when the backend doesn't have real data yet

export const MOCK_DEVICES = [
  {
    id: 'device_001',
    name: 'Main Field Sensor',
    location: 'North Field Section A',
    owner_id: 'user_001',
    type: 'irrigation_device',
    created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
    updated_at: new Date().toISOString(),
    is_active: true
  },
  {
    id: 'device_002',
    name: 'Greenhouse Sensor',
    location: 'Greenhouse Unit 3',
    owner_id: 'user_001',
    type: 'irrigation_device',
    created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
    updated_at: new Date().toISOString(),
    is_active: true
  },
  {
    id: 'device_003',
    name: 'Orchard Sensor',
    location: 'South Orchard Block C',
    owner_id: 'user_002',
    type: 'irrigation_device',
    created_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
    updated_at: new Date().toISOString(),
    is_active: true
  }
];

export const MOCK_SENSOR_READINGS = [
  {
    id: 'reading_001',
    device_id: 'device_001',
    soil_moisture: 45.2,
    temperature: 26.5,
    humidity: 62.1,
    timestamp: new Date(Date.now() - 300000).toISOString() // 5 minutes ago
  },
  {
    id: 'reading_002',
    device_id: 'device_001',
    soil_moisture: 43.8,
    temperature: 27.1,
    humidity: 60.5,
    timestamp: new Date(Date.now() - 600000).toISOString() // 10 minutes ago
  },
  {
    id: 'reading_003',
    device_id: 'device_002',
    soil_moisture: 38.7,
    temperature: 24.3,
    humidity: 68.9,
    timestamp: new Date(Date.now() - 300000).toISOString() // 5 minutes ago
  }
];

export const MOCK_IRRIGATION_EVENTS = [
  {
    id: 'event_001',
    device_id: 'device_001',
    start_time: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    end_time: new Date(Date.now() - 3300000).toISOString(), // 55 minutes ago
    duration_actual_minutes: 30,
    status: 'completed',
    created_at: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 'event_002',
    device_id: 'device_002',
    start_time: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
    end_time: new Date(Date.now() - 7020000).toISOString(), // 110 minutes ago
    duration_actual_minutes: 18,
    status: 'completed',
    created_at: new Date(Date.now() - 7200000).toISOString()
  }
];

export const MOCK_ALERTS = [
  {
    id: 'alert_001',
    device_id: 'device_001',
    alert_type: 'soil_moisture_low',
    severity: 'high',
    message: 'Soil moisture critically low: 28%',
    timestamp: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
    status: 'open',
    acknowledged_by: null,
    acknowledged_at: null,
    resolved_by: null,
    resolved_at: null
  },
  {
    id: 'alert_002',
    device_id: 'device_002',
    alert_type: 'device_error',
    severity: 'medium',
    message: 'Temperature high: 38°C',
    timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    status: 'acknowledged',
    acknowledged_by: 'user_001',
    acknowledged_at: new Date(Date.now() - 3500000).toISOString(), // Just acknowledged
    resolved_by: null,
    resolved_at: null
  }
];

export const MOCK_USERS = [
  {
    id: 'user_001',
    email: 'farmer@example.com',
    username: 'John Farmer',
    role: 'farmer',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date().toISOString(),
    is_active: true
  },
  {
    id: 'user_002',
    email: 'admin@example.com',
    username: 'Admin User',
    role: 'admin',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    updated_at: new Date().toISOString(),
    is_active: true
  }
];

// Function to generate dynamic mock sensor data
export function generateMockSensorReading(deviceId) {
  const baseValues = {
    'device_001': { moisture: 45, temp: 26, humidity: 62 },
    'device_002': { moisture: 38, temp: 24, humidity: 68 },
    'device_003': { moisture: 52, temp: 22, humidity: 70 }
  };

  const base = baseValues[deviceId] || baseValues['device_001'];
  
  // Add some random variation
  const moisture = Math.max(0, Math.min(100, base.moisture + (Math.random() * 10 - 5)));
  const temperature = Math.max(0, base.temp + (Math.random() * 5 - 2));
  const humidity = Math.max(0, Math.min(100, base.humidity + (Math.random() * 10 - 5)));

  return {
    id: `reading_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    device_id: deviceId,
    soil_moisture: parseFloat(moisture.toFixed(2)),
    temperature: parseFloat(temperature.toFixed(2)),
    humidity: parseFloat(humidity.toFixed(2)),
    timestamp: new Date().toISOString()
  };
}

// Function to generate dynamic mock alerts
export function generateMockAlert(deviceId) {
  const alertTypes = ['soil_moisture_low', 'device_error', 'unusual_reading'];
  const severities = ['low', 'medium', 'high'];
  
  const randomType = alertTypes[Math.floor(Math.random() * alertTypes.length)];
  const randomSeverity = severities[Math.floor(Math.random() * severities.length)];
  
  let message = '';
  if (randomType === 'soil_moisture_low') {
    message = `Soil moisture low: ${(Math.random() * 20).toFixed(1)}%`;
  } else if (randomType === 'device_error') {
    message = `Temperature high: ${(30 + Math.random() * 15).toFixed(1)}°C`;
  } else {
    message = `Unusual reading detected on device ${deviceId}`;
  }

  return {
    id: `alert_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    device_id: deviceId,
    alert_type: randomType,
    severity: randomSeverity,
    message,
    timestamp: new Date().toISOString(),
    status: 'open',
    acknowledged_by: null,
    acknowledged_at: null,
    resolved_by: null,
    resolved_at: null
  };
}