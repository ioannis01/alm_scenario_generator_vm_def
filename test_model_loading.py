#!/usr/bin/env python3
"""
Test script to diagnose model loading issue
"""

import sys
import os

print("="*60)
print("TESTING MODEL LOADING")
print("="*60)

# Test 1: Check if load_alm_data.py has get_available_model_ids
print("\n1. Checking load_alm_data.py...")
try:
    sys.path.insert(0, '/mnt/user-data/uploads')
    from load_alm_data import get_available_model_ids, get_database_connection
    print("✓ Successfully imported get_available_model_ids from load_alm_data")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test 2: Check database connection
print("\n2. Testing database connection...")
try:
    conn = get_database_connection()
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print("\nThis is likely the issue - check:")
    print("  - SQL Server is running")
    print("  - Connection settings in load_alm_data.py")
    print("  - ODBC Driver 17 for SQL Server is installed")
    sys.exit(1)

# Test 3: Try to get model IDs
print("\n3. Testing get_available_model_ids()...")
try:
    models = get_available_model_ids()
    print(f"✓ Success! Found {len(models)} models:")
    for m in models[:5]:
        print(f"   - {m['model_id']}: {m.get('contract_count', 0)} contracts, {m.get('counterparty_count', 0)} counterparties")
    
    if len(models) == 0:
        print("\n⚠ WARNING: No models found in database")
        print("Check if CONTRACT table has MODEL_ID values:")
        print("  SELECT DISTINCT MODEL_ID FROM dbo.CONTRACT WHERE MODEL_ID IS NOT NULL")
        
except Exception as e:
    print(f"✗ Error getting model IDs: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    print("\nThis means the function exists but fails when called.")
    print("Check the SQL query in get_available_model_ids()")
    sys.exit(1)

print("\n" + "="*60)
print("✓ ALL TESTS PASSED")
print("="*60)
print("\nThe backend works correctly.")
print("If the dropdown is still empty, the issue is in the frontend JavaScript.")
print("\nCheck browser console (F12) for errors.")
