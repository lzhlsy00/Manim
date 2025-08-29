"""
Supabase configuration and client setup for manimations project.
"""

import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Configuration class for Supabase integration."""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "video-generations")
        
        if not self.url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")
    
    def create_client(self) -> Client:
        """Create and return a Supabase client with service role permissions."""
        try:
            client = create_client(self.url, self.service_role_key)
            logger.info("Supabase client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {str(e)}")
            raise


# Global instance
_supabase_config: Optional[SupabaseConfig] = None


def get_supabase_config() -> SupabaseConfig:
    """Get the global Supabase configuration instance."""
    global _supabase_config
    if _supabase_config is None:
        _supabase_config = SupabaseConfig()
    return _supabase_config


def get_supabase_client() -> Client:
    """Get a configured Supabase client."""
    config = get_supabase_config()
    return config.create_client()


def get_storage_bucket_name() -> str:
    """Get the storage bucket name."""
    config = get_supabase_config()
    return config.storage_bucket