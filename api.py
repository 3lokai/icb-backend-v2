#!/usr/bin/env python
"""
FastAPI application for coffee scraping service.

This service provides a REST API interface to the existing coffee scraping scripts.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Coffee Scraping API",
    description="API for scraping coffee roaster and product data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and Response Models
class ScrapeRequest(BaseModel):
    name: str
    website_url: str
    options: List[str]  # ["roaster", "products"] or subset

class ScrapeResponse(BaseModel):
    success: bool
    roaster_data: Optional[Dict] = None
    products_data: List[Dict] = []
    total_products: int = 0
    errors: List[str] = []

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str = "1.0.0"

# Configuration
ROASTER_TIMEOUT = 120  # seconds
PRODUCTS_TIMEOUT = 300  # seconds
SCRIPT_DIR = Path(__file__).parent

def run_subprocess_with_timeout(cmd: List[str], timeout: int, description: str) -> tuple[bool, str, str]:
    """
    Run a subprocess with timeout and return success status, stdout, and stderr.
    
    Args:
        cmd: Command to run
        timeout: Timeout in seconds
        description: Description for logging
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        logger.info(f"Running {description}: {' '.join(cmd)}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=SCRIPT_DIR
        )
        
        elapsed = time.time() - start_time
        logger.info(f"{description} completed in {elapsed:.2f}s with return code {result.returncode}")
        
        if result.returncode == 0:
            return True, result.stdout, result.stderr
        else:
            logger.error(f"{description} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error(f"{description} timed out after {timeout}s")
        return False, "", f"Timeout after {timeout} seconds"
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False, "", str(e)

def read_json_file(file_path: Path) -> Optional[Dict]:
    """Read and parse a JSON file, returning None if file doesn't exist or is invalid."""
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully read JSON file: {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

async def scrape_roaster(name: str, website_url: str) -> tuple[bool, Optional[Dict], List[str]]:
    """
    Scrape roaster data using the existing roaster scraper script.
    
    Args:
        name: Roaster name
        website_url: Roaster website URL
        
    Returns:
        Tuple of (success, roaster_data, errors)
    """
    errors = []
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_output = Path(temp_file.name)
    
    try:
        # Run roaster scraper
        cmd = [
            "python", "run_roaster.py",
            "--single",
            "--input", f"{name},{website_url}",
            "--output", str(temp_output)
        ]
        
        success, stdout, stderr = run_subprocess_with_timeout(
            cmd, ROASTER_TIMEOUT, "roaster scraper"
        )
        
        if not success:
            errors.append(f"Roaster scraping failed: {stderr}")
            return False, None, errors
        
        # Read the output file
        roaster_data = read_json_file(temp_output)
        if roaster_data is None:
            errors.append("Failed to read roaster output file")
            return False, None, errors
        
        # The script saves as a list, so take the first item
        if isinstance(roaster_data, list) and len(roaster_data) > 0:
            roaster_data = roaster_data[0]
        
        logger.info(f"Successfully scraped roaster: {name}")
        return True, roaster_data, errors
        
    except Exception as e:
        errors.append(f"Unexpected error in roaster scraping: {e}")
        logger.error(f"Error scraping roaster {name}: {e}")
        return False, None, errors
    finally:
        # Clean up temporary file
        try:
            temp_output.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {temp_output}: {e}")

async def scrape_products(website_url: str) -> tuple[bool, List[Dict], List[str]]:
    """
    Scrape products data using the existing product scraper script.
    
    Args:
        website_url: Roaster website URL
        
    Returns:
        Tuple of (success, products_data, errors)
    """
    errors = []
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_output = Path(temp_file.name)
    
    try:
        # Run product scraper
        cmd = [
            "python", "run_product_scraper.py",
            "batch",
            "--roaster-link", website_url,
            "--output", str(temp_output)
        ]
        
        success, stdout, stderr = run_subprocess_with_timeout(
            cmd, PRODUCTS_TIMEOUT, "product scraper"
        )
        
        if not success:
            errors.append(f"Product scraping failed: {stderr}")
            return False, [], errors
        
        # Read the output file
        products_data = read_json_file(temp_output)
        if products_data is None:
            errors.append("Failed to read products output file")
            return False, [], errors
        
        # Ensure it's a list
        if not isinstance(products_data, list):
            products_data = [products_data]
        
        logger.info(f"Successfully scraped {len(products_data)} products from {website_url}")
        return True, products_data, errors
        
    except Exception as e:
        errors.append(f"Unexpected error in product scraping: {e}")
        logger.error(f"Error scraping products from {website_url}: {e}")
        return False, [], errors
    finally:
        # Clean up temporary file
        try:
            temp_output.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {temp_output}: {e}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time()
    )

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(request: ScrapeRequest):
    """
    Main scraping endpoint that can scrape roaster data, products, or both.
    
    Args:
        request: ScrapeRequest containing name, website_url, and options
        
    Returns:
        ScrapeResponse with scraped data and any errors
    """
    logger.info(f"Received scrape request for {request.name} ({request.website_url}) with options: {request.options}")
    
    response = ScrapeResponse(success=False, errors=[])
    
    # Validate options
    valid_options = {"roaster", "products"}
    invalid_options = set(request.options) - valid_options
    if invalid_options:
        response.errors.append(f"Invalid options: {invalid_options}. Valid options are: {valid_options}")
        return response
    
    if not request.options:
        response.errors.append("At least one option must be specified: 'roaster' or 'products'")
        return response
    
    # Scrape roaster data if requested
    if "roaster" in request.options:
        logger.info(f"Scraping roaster data for {request.name}")
        roaster_success, roaster_data, roaster_errors = await scrape_roaster(
            request.name, request.website_url
        )
        response.roaster_data = roaster_data
        response.errors.extend(roaster_errors)
        
        if not roaster_success:
            logger.warning(f"Roaster scraping failed for {request.name}")
    
    # Scrape products data if requested
    if "products" in request.options:
        logger.info(f"Scraping products data for {request.website_url}")
        products_success, products_data, products_errors = await scrape_products(
            request.website_url
        )
        response.products_data = products_data
        response.total_products = len(products_data)
        response.errors.extend(products_errors)
        
        if not products_success:
            logger.warning(f"Product scraping failed for {request.website_url}")
    
    # Determine overall success
    if "roaster" in request.options and "products" in request.options:
        # Both requested - need both to succeed
        roaster_success = response.roaster_data is not None
        products_success = len(response.products_data) > 0 or not response.errors
        response.success = roaster_success and products_success
    elif "roaster" in request.options:
        # Only roaster requested
        response.success = response.roaster_data is not None
    else:
        # Only products requested
        response.success = len(response.products_data) > 0 or not response.errors
    
    logger.info(f"Scrape request completed for {request.name}. Success: {response.success}")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail=f"Internal server error: {str(exc)}"
    )

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
