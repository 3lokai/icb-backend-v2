#!/bin/bash

# Coffee Scraping API - cURL Examples
# Make sure the API is running on http://localhost:8000

API_BASE_URL="http://localhost:8000"

echo "Coffee Scraping API - cURL Examples"
echo "==================================="
echo "Make sure the API is running on $API_BASE_URL"
echo "Start it with: python start_api.py"
echo ""

# Test health endpoint
echo "1. Testing Health Endpoint"
echo "--------------------------"
curl -X GET "$API_BASE_URL/health" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
echo ""

# Test roaster scraping only
echo "2. Testing Roaster Scraping Only"
echo "--------------------------------"
curl -X POST "$API_BASE_URL/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue Tokai",
    "website_url": "https://bluetokai.com",
    "options": ["roaster"]
  }' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
echo ""

# Test products scraping only
echo "3. Testing Products Scraping Only"
echo "---------------------------------"
curl -X POST "$API_BASE_URL/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue Tokai",
    "website_url": "https://bluetokai.com",
    "options": ["products"]
  }' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
echo ""

# Test both roaster and products
echo "4. Testing Both Roaster and Products"
echo "------------------------------------"
curl -X POST "$API_BASE_URL/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blue Tokai",
    "website_url": "https://bluetokai.com",
    "options": ["roaster", "products"]
  }' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
echo ""

# Test invalid request
echo "5. Testing Invalid Request"
echo "--------------------------"
curl -X POST "$API_BASE_URL/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Roaster",
    "website_url": "https://example.com",
    "options": ["invalid_option"]
  }' \
  -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n"
echo ""

echo "Examples completed!"
echo ""
echo "Note: The scraping operations may take several minutes to complete."
echo "You can monitor the API logs for progress information." 