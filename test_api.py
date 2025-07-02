#!/usr/bin/env python
"""
Test script for the Coffee Scraping API.

This script tests the API endpoints to ensure they work correctly.
"""

import asyncio
import json
import time
from typing import Dict, Any

import httpx

# API configuration
API_BASE_URL = "http://localhost:8000"

async def test_health_endpoint():
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            print(f"Health check status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Health response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Health check failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error testing health endpoint: {e}")
            return False

async def test_scrape_endpoint():
    """Test the scrape endpoint with a sample request."""
    print("\nTesting scrape endpoint...")
    
    # Test data
    test_request = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["roaster"]  # Start with just roaster to test
    }
    
    print(f"Test request: {json.dumps(test_request, indent=2)}")
    
    async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minute timeout
        try:
            start_time = time.time()
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=test_request
            )
            elapsed = time.time() - start_time
            
            print(f"Scrape response status: {response.status_code}")
            print(f"Request took {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Scrape response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Scrape request failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error testing scrape endpoint: {e}")
            return False

async def test_products_scrape():
    """Test scraping products specifically."""
    print("\nTesting products scraping...")
    
    test_request = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["products"]
    }
    
    print(f"Products test request: {json.dumps(test_request, indent=2)}")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            start_time = time.time()
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=test_request
            )
            elapsed = time.time() - start_time
            
            print(f"Products scrape response status: {response.status_code}")
            print(f"Request took {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Products scrape response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Products scrape request failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error testing products scrape: {e}")
            return False

async def test_both_scrape():
    """Test scraping both roaster and products."""
    print("\nTesting both roaster and products scraping...")
    
    test_request = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["roaster", "products"]
    }
    
    print(f"Both test request: {json.dumps(test_request, indent=2)}")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            start_time = time.time()
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=test_request
            )
            elapsed = time.time() - start_time
            
            print(f"Both scrape response status: {response.status_code}")
            print(f"Request took {elapsed:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Both scrape response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Both scrape request failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error testing both scrape: {e}")
            return False

async def test_invalid_request():
    """Test invalid request handling."""
    print("\nTesting invalid request handling...")
    
    # Test with invalid options
    invalid_request = {
        "name": "Test Roaster",
        "website_url": "https://example.com",
        "options": ["invalid_option"]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=invalid_request
            )
            
            print(f"Invalid request response status: {response.status_code}")
            
            if response.status_code == 200:  # Should still return 200 with error in response
                data = response.json()
                print(f"Invalid request response: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"Invalid request failed: {response.text}")
                return False
        except Exception as e:
            print(f"Error testing invalid request: {e}")
            return False

async def main():
    """Run all tests."""
    print("=" * 60)
    print("COFFEE SCRAPING API TEST SUITE")
    print("=" * 60)
    
    # Make sure the API is running
    print("Make sure the API is running on http://localhost:8000")
    print("You can start it with: python start_api.py")
    print()
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Roaster Scrape", test_scrape_endpoint),
        ("Products Scrape", test_products_scrape),
        ("Both Scrape", test_both_scrape),
        ("Invalid Request", test_invalid_request),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 