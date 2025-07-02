# Coffee Scraping API

A FastAPI application that provides a REST API interface to the existing coffee scraping scripts.

## Features

- **Single endpoint**: `POST /api/scrape` for scraping roaster and/or product data
- **Health check**: `GET /health` for monitoring API status
- **CORS support**: Configured for frontend integration
- **Production-ready**: Proper error handling, logging, and timeouts
- **Async processing**: Non-blocking scraping operations

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure all the existing scraping scripts are in place:
   - `run_roaster.py`
   - `run_product_scraper.py`

## Usage

### Starting the API Server

You can start the API server in two ways:

**Option 1: Using the startup script (recommended)**
```bash
python start_api.py
```

**Option 2: Direct uvicorn command**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### API Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "version": "1.0.0"
}
```

#### Scrape Data
```http
POST /api/scrape
```

**Request Body:**
```json
{
  "name": "Blue Tokai",
  "website_url": "https://bluetokai.com",
  "options": ["roaster", "products"]
}
```

**Parameters:**
- `name` (string, required): Name of the roaster
- `website_url` (string, required): Website URL to scrape
- `options` (array, required): Array of scraping options
  - `"roaster"`: Scrape roaster information
  - `"products"`: Scrape product data
  - Can include one or both options

**Response:**
```json
{
  "success": true,
  "roaster_data": {
    "name": "Blue Tokai",
    "website_url": "https://bluetokai.com",
    "description": "...",
    "location": "...",
    // ... other roaster fields
  },
  "products_data": [
    {
      "name": "Light Roast Coffee",
      "price": "₹450",
      "description": "...",
      // ... other product fields
    }
  ],
  "total_products": 15,
  "errors": []
}
```

**Response Fields:**
- `success` (boolean): Overall success status
- `roaster_data` (object, optional): Scraped roaster information
- `products_data` (array): Array of scraped products
- `total_products` (integer): Number of products scraped
- `errors` (array): Array of error messages

## Configuration

### Timeouts
The API uses configurable timeouts for different operations:
- **Roaster scraping**: 120 seconds
- **Product scraping**: 300 seconds

These can be modified in the `api.py` file:
```python
ROASTER_TIMEOUT = 120  # seconds
PRODUCTS_TIMEOUT = 300  # seconds
```

### CORS Settings
CORS is configured to allow all origins by default. For production, you should restrict this:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Testing

Run the test suite to verify the API functionality:

```bash
python test_api.py
```

**Prerequisites:**
- API server must be running on http://localhost:8000
- Internet connection for scraping tests

The test suite includes:
- Health check endpoint test
- Roaster scraping test
- Product scraping test
- Combined scraping test
- Invalid request handling test

## Error Handling

The API provides comprehensive error handling:

1. **Validation Errors**: Invalid request parameters are caught and returned with descriptive messages
2. **Scraping Errors**: Individual scraping failures are logged and included in the response
3. **Timeout Errors**: Long-running operations are terminated after the configured timeout
4. **System Errors**: Unhandled exceptions are caught and returned as 500 errors

## Logging

The API uses structured logging with the following levels:
- **INFO**: Normal operations and successful requests
- **WARNING**: Non-critical issues (e.g., scraping failures)
- **ERROR**: Critical errors and exceptions

Logs include:
- Request details (roaster name, URL, options)
- Scraping progress and timing
- Error details with stack traces
- Subprocess output for debugging

## Production Deployment

### Environment Variables
Set appropriate environment variables for production:
```bash
export PYTHONPATH=/path/to/your/project
export LOG_LEVEL=INFO
```

### Process Management
Use a process manager like `systemd` or `supervisor`:

**systemd service example:**
```ini
[Unit]
Description=Coffee Scraping API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/usr/bin/python3 start_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Reverse Proxy
Use nginx or Apache as a reverse proxy:

**nginx configuration example:**
```nginx
server {
    listen 80;
    server_name your-api-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed and the Python path is correct
2. **Permission Errors**: Ensure the API has permission to create temporary files
3. **Timeout Errors**: Increase timeout values for slow websites
4. **Memory Issues**: Monitor memory usage during large scraping operations

### Debug Mode
Enable debug logging by modifying the logging level in `api.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing
Test individual components:
```bash
# Test roaster scraper directly
python run_roaster.py --single --input "Test Roaster,https://example.com"

# Test product scraper directly
python run_product_scraper.py batch --roaster-link "https://example.com"
```

## API Documentation

Interactive API documentation is available at http://localhost:8000/docs when the server is running. This provides:
- Endpoint descriptions
- Request/response schemas
- Interactive testing interface
- Example requests and responses

## Contributing

When contributing to the API:

1. Follow the existing code style and patterns
2. Add appropriate logging for new functionality
3. Include error handling for all new endpoints
4. Update tests for any new features
5. Update this documentation for any changes

## License

This API is part of the coffee scraping project and follows the same license terms. 