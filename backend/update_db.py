#!/usr/bin/env python
"""
Update existing irrigation_events records with mode and water_used_liters
"""
import os
from app.services.postgres_service import postgres_service

def update_existing_records():
    print("Updating existing irrigation_events records...")
    
    # Update mode for records where mode is NULL
    print("\n1. Updating mode based on user_triggered...")
    sql1 = """
    UPDATE irrigation_events 
    SET mode = CASE WHEN user_triggered = TRUE THEN 'manual' ELSE 'auto' END 
    WHERE mode IS NULL;
    """
    result1 = postgres_service.execute(sql1)
    print("✅ Mode update complete")
    
    # Update water_used_liters for records where it's NULL
    print("\n2. Updating water_used_liters based on duration...")
    sql2 = """
    UPDATE irrigation_events 
    SET water_used_liters = duration_actual_seconds * 0.05 
    WHERE water_used_liters IS NULL AND duration_actual_seconds IS NOT NULL;
    """
    result2 = postgres_service.execute(sql2)
    print("✅ Water usage update complete")
    
    # Check results
    print("\n3. Verifying updates...")
    verify_sql = """
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN mode IS NOT NULL THEN 1 END) as with_mode,
        COUNT(CASE WHEN water_used_liters IS NOT NULL THEN 1 END) as with_water
    FROM irrigation_events;
    """
    result = postgres_service.execute(verify_sql, fetchone=True)
    print(f"   Total records: {result['total']}")
    print(f"   Records with mode: {result['with_mode']}")
    print(f"   Records with water: {result['with_water']}")
    
    if result['total'] == result['with_mode'] == result['with_water']:
        print("\n✅ All records updated successfully!")
    else:
        print("\n⚠️ Some records still have NULL values")

if __name__ == '__main__':
    try:
        update_existing_records()
    except Exception as e:
        print(f"❌ Error: {e}")
