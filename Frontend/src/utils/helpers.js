// Utility functions for AgriSense

// Format date and time
export const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
};

export const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
};

export const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

// Format duration in seconds to human readable format
export const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
};

// Format number to 2 decimal places
export const formatNumber = (num, decimals = 2) => {
    return parseFloat(num).toFixed(decimals);
};

// Calculate time difference in minutes
export const minutesDiff = (date1, date2) => {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    const diffMs = Math.abs(d2 - d1);
    return Math.round(diffMs / 60000);
};

// Check if a value is within a range
export const isInRange = (value, min, max) => {
    return value >= min && value <= max;
};

// Debounce function to limit rate of function calls
export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Throttle function to limit rate of function calls
export const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Generate a random ID
export const generateId = () => {
    return Math.random().toString(36).substr(2, 9);
};

// Capitalize first letter of a string
export const capitalize = (str) => {
    if (!str) return str;
    return str.charAt(0).toUpperCase() + str.slice(1);
};

// Convert snake_case to Title Case
export const snakeToTitleCase = (snakeStr) => {
    if (!snakeStr) return snakeStr;
    return snakeStr
        .split('_')
        .map(word => capitalize(word))
        .join(' ');
};

// Format file size
export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Validate email format
export const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
};

// Validate phone number
export const validatePhone = (phone) => {
    const re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone.replace(/[\s\-\(\)]/g, ''));
};

// Escape HTML to prevent XSS
export const escapeHtml = (text) => {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };

    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
};

// Deep clone an object
export const deepClone = (obj) => {
    return JSON.parse(JSON.stringify(obj));
};

// Check if browser supports required features
export const checkBrowserSupport = () => {
    const requiredFeatures = [
        'fetch',
        'Promise',
        'localStorage',
        'JSON',
        'Map',
        'Set',
        'Array.from',
        'Object.assign'
    ];

    const unsupported = [];
    for (const feature of requiredFeatures) {
        if (!(feature in window) && !(feature in Array) && !(feature in Object)) {
            const obj = feature.includes('.') ? window[feature.split('.')[0]] : window;
            const prop = feature.includes('.') ? feature.split('.')[1] : feature;
            if (!obj || !(prop in obj)) {
                unsupported.push(feature);
            }
        }
    }

    return {
        supported: unsupported.length === 0,
        unsupported: unsupported
    };
};

// Show a toast notification
export const showToast = (message, type = 'info', duration = 3000) => {
    // Create toast element if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        toastContainer.style.display = 'flex';
        toastContainer.style.flexDirection = 'column';
        toastContainer.style.alignItems = 'flex-end';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} fade show`;
    toast.style.minWidth = '300px';
    toast.style.marginBottom = '10px';
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>${message}</div>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto remove toast after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 150);
        }
    }, duration);
};

// Simple template engine
export const renderTemplate = (template, data) => {
    return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
        return data[key] !== undefined ? data[key] : match;
    });
};
