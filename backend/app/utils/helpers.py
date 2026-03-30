import hashlib
import secrets
from datetime import datetime
from typing import Dict, Any


def generate_device_id():
    """Generate a unique device ID"""
    return f"device_{secrets.token_hex(8)}"


def hash_data(data: str) -> str:
    """Hash data using SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()


def format_timestamp(timestamp: datetime) -> str:
    """Format datetime object to ISO string"""
    return timestamp.isoformat()


import math
from typing import Dict, Any, Optional

def calculate_dew_point(temperature: Optional[float], humidity: Optional[float]) -> Optional[float]:
    """Calculate dew point from temperature and humidity"""
    if temperature is None or humidity is None:
        return None
    # Simplified Magnus formula
    a = 17.27
    b = 237.7
    # Protect against zero humidity for log calculation
    h = max(0.01, humidity)
    alpha = ((a * temperature) / (b + temperature)) + math.log(h / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return round(dew_point, 2)


def calculate_heat_index(temperature: Optional[float], humidity: Optional[float]) -> Optional[float]:
    """Calculate heat index from temperature and humidity"""
    if temperature is None or humidity is None:
        return None
    # Simplified calculation
    if temperature < 27:  # Below 80°F
        return temperature
    
    # Using Rothfusz regression
    hi = (
        -42.379 +
        2.04901523 * temperature +
        10.14333127 * humidity -
        0.22475541 * temperature * humidity -
        0.00683783 * temperature * temperature -
        0.05481717 * humidity * humidity +
        0.00122874 * temperature * temperature * humidity +
        0.00085282 * temperature * humidity * humidity -
        0.00000199 * temperature * temperature * humidity * humidity
    )
    
    # Adjustment for high humidity and low temperatures
    if humidity < 13 and 80 <= temperature <= 112:
        adj = ((13 - humidity) / 4) * ((17 - abs(temperature - 95)) / 17) ** 0.5
        hi -= adj
    elif humidity > 85 and 80 <= temperature <= 87:
        adj = ((humidity - 85) / 10) * ((87 - temperature) / 5)
        hi += adj
    
    return round(hi, 2)