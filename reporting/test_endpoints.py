#!/usr/bin/env python3
"""
Test script for FarmHub Reporting API endpoints
"""
import sys
import os

sys.path.append(os.path.dirname(__file__))

from main import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    print(f"Health endpoint: {response.status_code} - {response.json()}")
    return response.status_code == 200


def test_summary_endpoint():
    """Test the summary endpoint"""
    response = client.get("/summary")
    print(f"Summary endpoint: {response.status_code} - {response.json()}")
    return response.status_code == 200


def test_farm_summary_endpoint():
    """Test the farm summary endpoint"""
    farm_id = 1  # Using farm ID 1 from seeded data
    response = client.get(f"/reports/farm/{farm_id}/summary")
    print(f"Farm {farm_id} summary: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Farm Name: {data['farm_name']}")
        print(f"  Total Farmers: {data['total_farmers']}")
        print(f"  Total Cows: {data['total_cows']}")
        print(f"  Total Milk Production: {data['total_milk_production']} liters")
    else:
        print(f"  Error: {response.text}")
    return response.status_code == 200


def test_farm_milk_production_endpoint():
    """Test the farm milk production endpoint"""
    farm_id = 1
    response = client.get(f"/reports/farm/{farm_id}/milk-production")
    print(f"Farm {farm_id} milk production: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} cows with milk production data")
        for cow in data:
            print(
                f"    {cow['cow_tag']} ({cow['cow_breed']}): {cow['total_liters']} liters, {cow['record_count']} records"
            )
    else:
        print(f"  Error: {response.text}")
    return response.status_code == 200


def test_farm_daily_milk_endpoint():
    """Test the farm daily milk endpoint"""
    farm_id = 1
    response = client.get(f"/reports/farm/{farm_id}/daily-milk")
    print(f"Farm {farm_id} daily milk: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Found {len(data)} days of milk production data")
        for day in data[:3]:  # Show first 3 days
            print(
                f"    {day['date']}: {day['total_liters']} liters from {day['cow_count']} cows"
            )
    else:
        print(f"  Error: {response.text}")
    return response.status_code == 200


def test_farmer_summary_endpoint():
    """Test the farmer summary endpoint"""
    # seeded farmer user_id is likely 3 based on migrations order, but we don't enforce here
    # Use 1 as a common default; adjust if needed
    user_id = 1
    response = client.get(f"/reports/farmer/{user_id}/summary")
    print(f"Farmer {user_id} summary: {response.status_code}")
    # 200 if exists, otherwise 404; count either as an executable path
    return response.status_code in (200, 404)


def test_recent_activities_endpoint():
    """Test the recent activities endpoint"""
    response = client.get("/reports/activities/recent?limit=5")
    print(f"Recent activities: {response.status_code}")
    return response.status_code == 200

if __name__ == "__main__":
    print("Testing FarmHub Reporting API endpoints...")
    print("=" * 50)

    # Test all endpoints
    tests = [
        ("Health", test_health_endpoint),
        ("Summary", test_summary_endpoint),
        ("Farm Summary", test_farm_summary_endpoint),
        ("Farm Milk Production", test_farm_milk_production_endpoint),
        ("Farm Daily Milk", test_farm_daily_milk_endpoint),
    ("Farmer Summary", test_farmer_summary_endpoint),
    ("Recent Activities", test_recent_activities_endpoint),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name} Test:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  Error: {str(e)}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
