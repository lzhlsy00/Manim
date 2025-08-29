"""
Helper utility functions for Manimations API.
"""

import os
import time
import uuid
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def generate_animation_id() -> str:
    """Generate a unique animation ID."""
    return str(uuid.uuid4())


def cleanup_temp_files(animation_id: str) -> None:
    """Clean up temporary files for a given animation ID."""
    temp_paths = [
        f"temp_scripts/{animation_id}.py",
        f"temp_output/{animation_id}",
        f"temp_output/{animation_id}_audio.mp3",
        f"temp_output/{animation_id}_synced_audio.mp3"
    ]
    
    for path in temp_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
                logger.debug(f"Cleaned up file: {path}")
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                logger.debug(f"Cleaned up directory: {path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {path}: {str(e)}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.1f}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{int(hours)}h {int(remaining_minutes)}m {remaining_seconds:.1f}s"


def log_performance(func_name: str, start_time: float, end_time: float) -> None:
    """Log performance metrics for a function."""
    duration = end_time - start_time
    logger.info(f"{func_name} completed in {format_duration(duration)}")


def validate_prompt(prompt: str) -> bool:
    """Validate that a prompt is suitable for animation generation."""
    if not prompt or not prompt.strip():
        return False
    
    if len(prompt.strip()) < 3:
        return False
    
    # Check for potentially problematic content
    problematic_keywords = ['hack', 'exploit', 'malicious', 'virus']
    prompt_lower = prompt.lower()
    
    for keyword in problematic_keywords:
        if keyword in prompt_lower:
            logger.warning(f"Potentially problematic keyword '{keyword}' found in prompt")
            return False
    
    return True


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0


def create_error_response(error_message: str, error_type: str = "GenerationError") -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": error_type,
        "message": error_message,
        "timestamp": time.time()
    }