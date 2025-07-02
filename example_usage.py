#!/usr/bin/env python
"""
Example usage of the Coffee Scraping API.

This script demonstrates how to use the API from Python code.
"""

import asyncio
import json
import httpx
from typing import Dict, Any

# API configuration
API_BASE_URL = "http://localhost:8000"

async def scrape_roaster_only():
    """Example: Scrape only roaster information."""
    print("=" * 50)
    print("EXAMPLE 1: Scrape Roaster Information Only")
    print("=" * 50)
    
    request_data = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["roaster"]
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data['success']}")
                print(f"Roaster Data: {json.dumps(data['roaster_data'], indent=2)}")
                print(f"Errors: {data['errors']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

async def scrape_products_only():
    """Example: Scrape only product information."""
    print("\n" + "=" * 50)
    print("EXAMPLE 2: Scrape Products Only")
    print("=" * 50)
    
    request_data = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["products"]
    }
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data['success']}")
                print(f"Total Products: {data['total_products']}")
                print(f"First Product: {json.dumps(data['products_data'][0] if data['products_data'] else {}, indent=2)}")
                print(f"Errors: {data['errors']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

async def scrape_both():
    """Example: Scrape both roaster and product information."""
    print("\n" + "=" * 50)
    print("EXAMPLE 3: Scrape Both Roaster and Products")
    print("=" * 50)
    
    request_data = {
        "name": "Blue Tokai",
        "website_url": "https://bluetokai.com",
        "options": ["roaster", "products"]
    }
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/scrape",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data['success']}")
                print(f"Roaster Name: {data['roaster_data']['name'] if data['roaster_data'] else 'N/A'}")
                print(f"Total Products: {data['total_products']}")
                print(f"Errors: {data['errors']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

async def check_health():
    """Example: Check API health."""
    print("\n" + "=" * 50)
    print("EXAMPLE 4: Health Check")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Status: {data['status']}")
                print(f"Version: {data['version']}")
                print(f"Timestamp: {data['timestamp']}")
            else:
                print(f"Health check failed: {response.status_code}")
                
        except Exception as e:
            print(f"Exception: {e}")

async def handle_errors():
    """Example: Handle invalid requests."""
    print("\n" + "=" * 50)
    print("EXAMPLE 5: Error Handling")
    print("=" * 50)
    
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
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data['success']}")
                print(f"Errors: {data['errors']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

async def main():
    """Run all examples."""
    print("COFFEE SCRAPING API - USAGE EXAMPLES")
    print("Make sure the API is running on http://localhost:8000")
    print("Start it with: python start_api.py")
    print()
    
    # Check if API is available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ API is not responding. Please start the API server first.")
                return
    except Exception:
        print("❌ Cannot connect to API. Please start the API server first.")
        print("Run: python start_api.py")
        return
    
    print("✅ API is available. Running examples...\n")
    
    # Run examples
    await check_health()
    await scrape_roaster_only()
    await scrape_products_only()
    await scrape_both()
    await handle_errors()
    
    print("\n" + "=" * 50)
    print("EXAMPLES COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 