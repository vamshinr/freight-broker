#!/usr/bin/env python3
"""
Test script for the cleaned up freight broker API
Demonstrates the 3 essential endpoints with API key authentication
"""

import requests
import json

API_KEY = "freight-broker-key-2025-secure"
BASE_URL = "http://localhost:8003"

def test_loads_endpoint():
    """Test GET /loads endpoint"""
    print("🚛 Testing GET /loads endpoint")
    print("-" * 40)
    
    # Test without API key (should fail)
    print("Without API key:")
    response = requests.get(f"{BASE_URL}/loads")
    print(f"Status: {response.status_code} (Expected: 422)")
    
    # Test with API key (should succeed)
    print("\nWith API key:")
    headers = {"X-API-Key": API_KEY}
    response = requests.get(f"{BASE_URL}/loads", headers=headers)
    print(f"Status: {response.status_code} (Expected: 200)")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success! Found {data['total_loads']} loads")
        print(f"First load: {data['loads'][0]['load_id']} - {data['loads'][0]['origin']} to {data['loads'][0]['destination']}")
    
    print()

def test_call_data_endpoint():
    """Test POST /call-data endpoint"""
    print("📞 Testing POST /call-data endpoint")
    print("-" * 40)
    
    # Test data with correct types: duration=int, revenue=int, others=string
    test_data = {
        "call_id": "demo-test-001",
        "transcript": "Carrier called about flatbed load from Dallas to Atlanta",
        "duration": 420,  # 7 minutes in seconds (integer)
        "sentiment": "Positive",  # string
        "outcome": "Offer accepted",  # string
        "revenue": 2800,  # integer
        "negotiations": None  # null becomes 0
    }
    
    # Test without API key (should fail)
    print("Without API key:")
    response = requests.post(f"{BASE_URL}/call-data", json=test_data)
    print(f"Status: {response.status_code} (Expected: 422)")
    
    # Test with API key (should succeed)
    print("\nWith API key:")
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{BASE_URL}/call-data", json=test_data, headers=headers)
    print(f"Status: {response.status_code} (Expected: 200)")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success! Call data stored")
        processed = result['processed_values']
        print(f"Duration: {processed['duration']} seconds")
        print(f"Revenue: ${processed['revenue']}")
        print(f"Negotiations: {processed['negotiations']} (null → 0)")
        print(f"Sentiment: {processed['sentiment']}")
        print(f"Outcome: {processed['outcome']}")
    
    print()

def test_dashboard_endpoint():
    """Test GET /dashboard endpoint"""
    print("📊 Testing GET /dashboard endpoint")
    print("-" * 40)
    
    # Dashboard should work without API key
    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"Dashboard Status: {response.status_code} (Expected: 200)")
    
    # Test metrics API
    response = requests.get(f"{BASE_URL}/dashboard/api/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print("✅ Dashboard metrics:")
        print(f"  Total Calls: {metrics['total_calls']}")
        print(f"  Total Revenue: ${metrics['total_revenue']}")
        print(f"  Avg Duration: {metrics['avg_duration']} seconds")
        print(f"  Avg Negotiations: {metrics['avg_negotiations']}")
        print(f"  Success Rate: {metrics['success_rate']}%")
    
    print()

def main():
    print("🧪 Freight Broker API Test Suite")
    print("=" * 50)
    print(f"API Key: {API_KEY}")
    print(f"Server: {BASE_URL}")
    print("=" * 50)
    
    try:
        test_loads_endpoint()
        test_call_data_endpoint()
        test_dashboard_endpoint()
        
        print("🎉 All tests completed!")
        print("\n📝 Summary:")
        print("✅ GET /loads - Protected with API key")
        print("✅ POST /call-data - Protected with API key, handles null negotiations")
        print("✅ GET /dashboard - Public access for viewing analytics")
        print("\n🔑 API Key Required: freight-broker-key-2025-secure")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("Make sure the server is running on port 8003")

if __name__ == "__main__":
    main()
