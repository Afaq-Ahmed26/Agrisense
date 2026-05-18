#!/usr/bin/env python
"""Query irrigation events to verify updates"""
from app.services.postgres_service import postgres_service

sql = """
SELECT 
    id, 
    mode, 
    user_triggered, 
    water_used_liters, 
    status,
    duration_actual_seconds,
    created_at
FROM irrigation_events 
ORDER BY created_at DESC 
LIMIT 3;
"""

rows = postgres_service.execute(sql, fetchall=True)

print("\nLatest 3 Irrigation Events:")
print("=" * 100)

if rows:
    for row in rows:
        print(f"ID: {row['id']}")
        print(f"  Mode: {row['mode']} | User Triggered: {row['user_triggered']} | Status: {row['status']}")
        print(f"  Duration: {row['duration_actual_seconds']}s | Water: {row['water_used_liters']} L")
        print(f"  Created: {row['created_at']}")
        print()
else:
    print("No records found")
