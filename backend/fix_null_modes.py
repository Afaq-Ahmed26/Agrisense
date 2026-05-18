#!/usr/bin/env python
"""Fix NULL mode values in recent records"""
from app.services.postgres_service import postgres_service

sql = """
UPDATE irrigation_events 
SET mode = CASE WHEN user_triggered = TRUE THEN 'manual' ELSE 'auto' END 
WHERE mode IS NULL;
"""

result = postgres_service.execute(sql)
print("✅ Updated all NULL mode values")

# Verify
verify_sql = """
SELECT COUNT(*) as null_modes FROM irrigation_events WHERE mode IS NULL;
"""
result = postgres_service.execute(verify_sql, fetchone=True)
print(f"Remaining NULL modes: {result['null_modes']}")

# Show results
sql2 = """
SELECT id, mode, user_triggered, water_used_liters, status FROM irrigation_events ORDER BY created_at DESC LIMIT 3;
"""
rows = postgres_service.execute(sql2, fetchall=True)

print("\nLatest 3 Events After Fix:")
print("=" * 80)
for row in rows:
    print(f"ID: {row['id'][:20]}...")
    print(f"  Mode: {row['mode']} | User Triggered: {row['user_triggered']} | Status: {row['status']}")
    print(f"  Water: {row['water_used_liters']} L\n")
