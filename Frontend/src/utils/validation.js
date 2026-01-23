// Validation utilities for AgriSense frontend

export const ValidationUtils = {
  // Password validation function
  password: (password) => {
    if (!password) {
      return 'Password is required';
    }
    
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    
    if (!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    
    if (!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    
    if (!/\d/.test(password)) {
      return 'Password must contain at least one digit';
    }
    
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return 'Password must contain at least one special character';
    }
    
    return null; // Valid password
  },

  // Email validation function
  email: (email) => {
    if (!email) {
      return 'Email is required';
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Please enter a valid email address';
    }
    
    return null; // Valid email
  },

  // Device ID validation
  deviceId: (deviceId) => {
    if (!deviceId) {
      return 'Device ID is required';
    }
    
    if (typeof deviceId !== 'string' || deviceId.length < 3) {
      return 'Device ID must be a string of at least 3 characters';
    }
    
    return null; // Valid device ID
  },

  // Numeric value validation
  numeric: (value, min = null, max = null) => {
    if (value === null || value === undefined || value === '') {
      return 'Value is required';
    }
    
    const numValue = Number(value);
    if (isNaN(numValue)) {
      return 'Value must be a number';
    }
    
    if (min !== null && numValue < min) {
      return `Value must be at least ${min}`;
    }
    
    if (max !== null && numValue > max) {
      return `Value must not exceed ${max}`;
    }
    
    return null; // Valid numeric value
  }
};