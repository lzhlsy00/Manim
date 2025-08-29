"""
Configuration and environment setup for Manimations API.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('manimations.log'),
            logging.StreamHandler()
        ]
    )


def load_environment():
    """Load environment variables from .env file."""
    # Look for .env file in current directory first, then parent directories
    env_path = Path(".env")
    if not env_path.exists():
        # Try parent directory (useful for development)
        env_path = Path("../.env")
    
    if env_path.exists():
        load_dotenv(env_path)
        logging.info(f"Loaded environment from {env_path.absolute()}")
    else:
        logging.warning("No .env file found. Make sure to set environment variables manually.")


def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "generated_videos",
        "temp_scripts", 
        "temp_output"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def validate_environment():
    """Validate that required environment variables are set."""
    # Load environment variables from .env file first
    load_environment()
    
    required_vars = ["ANTHROPIC_API_KEY"]
    optional_vars = ["OPENAI_API_KEY"]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_required)}\n"
            "Please add these to your .env file or set them manually."
        )
    
    if missing_optional:
        logging.warning(
            f"Missing optional environment variables: {', '.join(missing_optional)}\n"
            "Some features may be unavailable. Add them to your .env file if needed."
        )


def get_app_config():
    """Get application configuration."""
    # Load environment first
    load_environment()
    
    return {
        "title": "Manimations API",
        "description": "Educational animation generator using Manim and Claude AI",
        "version": "1.0.0",
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", "8000"))
    }