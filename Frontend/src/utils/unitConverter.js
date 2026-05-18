/**
 * Unit conversion utilities for AgriSense
 */

// Temperature conversions
export const convertTemperature = (value, fromUnit, toUnit) => {
    if (fromUnit === toUnit) return value;
    
    // Convert to Celsius first
    let celsiusValue;
    if (fromUnit === 'Fahrenheit') {
        celsiusValue = (value - 32) * 5/9;
    } else if (fromUnit === 'Kelvin') {
        celsiusValue = value - 273.15;
    } else { // Already in Celsius
        celsiusValue = value;
    }
    
    // Convert to target unit
    if (toUnit === 'Fahrenheit') {
        return (celsiusValue * 9/5) + 32;
    } else if (toUnit === 'Kelvin') {
        return celsiusValue + 273.15;
    } else { // To Celsius
        return celsiusValue;
    }
};

// Volume conversions
export const convertVolume = (value, fromUnit, toUnit) => {
    if (fromUnit === toUnit) return value;
    
    // Convert to liters first
    let litersValue;
    if (fromUnit === 'Gallons') {
        litersValue = value * 3.78541; // US gallons to liters
    } else if (fromUnit === 'Milliliters') {
        litersValue = value / 1000;
    } else { // Already in liters
        litersValue = value;
    }
    
    // Convert to target unit
    if (toUnit === 'Gallons') {
        return litersValue / 3.78541;
    } else if (toUnit === 'Milliliters') {
        return litersValue * 1000;
    } else { // To liters
        return litersValue;
    }
};

// Format value with user's preferred unit
export const formatWithUserPreferences = (value, valueType, userPreferences) => {
    // If user preferences are not provided, use defaults
    const preferences = userPreferences || {
        temperature_unit: 'Celsius',
        volume_unit: 'liters',
        time_zone: 'UTC',
        notification_sound: 'default'
    };
    
    let convertedValue = value;
    let unitSymbol = '';
    
    switch(valueType) {
        case 'temperature':
            convertedValue = convertTemperature(value, 'Celsius', preferences.temperature_unit);
            unitSymbol = preferences.temperature_unit === 'Celsius' ? '°C' : 
                        preferences.temperature_unit === 'Fahrenheit' ? '°F' : 'K';
            // Ensure default is Celsius, not Kelvin
            if (!['Celsius', 'Fahrenheit', 'Kelvin'].includes(preferences.temperature_unit)) {
                unitSymbol = '°C';
                convertedValue = value;
            }
            break;
        case 'volume':
            convertedValue = convertVolume(value, 'liters', preferences.volume_unit);
            unitSymbol = preferences.volume_unit === 'liters' ? 'L' : 
                        preferences.volume_unit === 'Gallons' ? 'gal' : 'mL';
            break;
        case 'humidity':
            unitSymbol = '%';
            break;
        case 'moisture':
            unitSymbol = '%';
            break;
        case 'light':
            unitSymbol = ' lx';
            break;
        default:
            break;
    }
    
    return {
        value: convertedValue,
        unit: unitSymbol,
        formatted: `${convertedValue.toFixed(2)}${unitSymbol}`
    };
};