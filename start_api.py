#!/usr/bin/env python
"""
Startup script for the Coffee Scraping API.

This script provides a convenient way to start the FastAPI server with proper configuration.
"""

import os
import uvicorn
from api import app

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print("Starting Coffee Scraping API...")
    print(f"API will be available at: http://{host}:{port}")
    print(f"API documentation at: http://{host}:{port}/docs")
    print(f"Health check at: http://{host}:{port}/health")
    
    if reload:
        print("Development mode: auto-reload enabled")
        print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    ) 