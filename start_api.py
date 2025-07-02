#!/usr/bin/env python
"""
Startup script for the Coffee Scraping API.

This script provides a convenient way to start the FastAPI server with proper configuration.
"""

import uvicorn
from api import app

if __name__ == "__main__":
    print("Starting Coffee Scraping API...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Health check at: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 