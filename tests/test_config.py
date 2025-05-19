import os
import shutil
import tempfile
import types
import pytest
from pathlib import Path

import sys
from pathlib import Path
# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as config_module

# Utility to patch environment variables
def patch_env(monkeypatch, env_vars):
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

# Utility to create a temporary .env file
def create_temp_env_file(tmp_path, content):
    env_path = tmp_path / ".env"
    env_path.write_text(content)
    return env_path

def test_supabase_config_from_env_success(monkeypatch):
    patch_env(monkeypatch, {"SUPABASE_URL": "https://test.supabase.io", "SUPABASE_KEY": "secret"})
    cfg = config_module.SupabaseConfig.from_env()
    assert cfg.url == "https://test.supabase.io"
    assert cfg.key == "secret"

def test_supabase_config_from_env_missing(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    with pytest.raises(ValueError):
        config_module.SupabaseConfig.from_env()

def test_cache_dir_created(tmp_path, monkeypatch):
    # Patch CACHE_DIR env and reload config.py
    cache_dir = tmp_path / "mycache"
    monkeypatch.setenv("CACHE_DIR", str(cache_dir))
    # Remove the dir if it exists
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    # Reload config.py to trigger directory creation
    import importlib
    importlib.reload(config_module)
    assert cache_dir.exists()
    # Clean up
    shutil.rmtree(cache_dir)

def test_supabase_url_from_env():
    # This test checks the actual .env file in the project root
    expected_url = "https://xrgmpplicqnlyowbhhrj.supabase.co"
    cfg = config_module.SupabaseConfig.from_env()
    assert cfg.url == expected_url

def test_config_from_env(monkeypatch):
    # Set all necessary env vars
    patch_env(monkeypatch, {
        "SUPABASE_URL": "https://test.supabase.io",
        "SUPABASE_KEY": "secret",
        "USER_AGENT": "test-agent",
        "REQUEST_TIMEOUT": "10",
        "OPENAI_API_KEY": "oa-key",
        "DEEPSEEK_API_KEY": "ds-key"
    })
    # Patch Config.from_env to not raise
    config = config_module.Config.from_env()
    assert config.supabase.url == "https://test.supabase.io"
    assert config.supabase.key == "secret"
    assert hasattr(config, "scraper")
    assert hasattr(config, "llm")
    assert config.llm.openai_api_key == "oa-key"
    assert config.llm.deepseek_api_key == "ds-key"
