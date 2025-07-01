"""
Configuration module for the Coffee Scraper.
Handles all environment variables and project settings.
"""

from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

# Debug: Print script and working directory info
print("[DEBUG] Script directory:", Path(__file__).parent.resolve())
print("[DEBUG] Current working directory:", Path.cwd())
print("[DEBUG] .env exists in script dir:", (Path(__file__).parent / ".env").exists())

# Debug: Print contents of .env file if it exists
if (Path(__file__).parent / ".env").exists():
    with open(Path(__file__).parent / ".env", "r") as f:
        print("[DEBUG] Contents of .env being loaded:\n" + f.read())

# Always load .env at the very top
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

print("DEBUG: All environment variables:")
for k, v in os.environ.items():
    if "KEY" in k or "OPENAI" in k:
        print(f"{k}={v}")

# Determine environment (dev, test, prod, etc.)
ENV = os.getenv("ENV", "dev")

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Cache directory
CACHE_DIR = Path(os.getenv("CACHE_DIR", "./cache"))
CACHE_DIR.mkdir(exist_ok=True)


class SupabaseConfig(BaseModel):
    """Supabase configuration settings."""

    url: str
    key: str

    @classmethod
    def from_env(cls):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
        return cls(url=url, key=key)


class ScraperConfig(BaseModel):
    """General scraper configuration settings."""

    user_agent: str
    request_timeout: int


class LLMConfig(BaseModel):
    """LLM API configuration for enrichment."""

    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

# Main configuration object
class Config(BaseModel):
    """
    Main configuration class for the Coffee Scraper.
    Loads and validates all environment variables and settings.
    Supports environment selection (dev, test, prod) via ENV variable.
    """

    supabase: SupabaseConfig
    scraper: ScraperConfig
    llm: LLMConfig
    CACHE_DIR: Path = CACHE_DIR
    ENV: str = ENV

    @classmethod
    def from_env(cls):
        """
        Create configuration from environment variables.
        Raises clear errors if required variables are missing.
        """
        return cls(
            supabase=SupabaseConfig.from_env(),
            scraper=ScraperConfig(
                user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            ),
            llm=LLMConfig(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            ),
        )


# Create config instance for importing in other modules
config = Config.from_env()
