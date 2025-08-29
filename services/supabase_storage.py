"""
Supabase Storage service for uploading and managing video files.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from utils.supabase_config import get_supabase_client, get_storage_bucket_name

logger = logging.getLogger(__name__)


async def upload_video_to_supabase(video_path: str, video_id: str) -> Optional[str]:
    """
    Upload a video file to Supabase Storage and return the public URL.
    
    Args:
        video_path: Local path to the video file
        video_id: Unique identifier for the video
        
    Returns:
        Public URL of the uploaded video or None if upload failed
    """
    try:
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
        
        # Get Supabase client and bucket name
        supabase = get_supabase_client()
        bucket_name = get_storage_bucket_name()
        
        # Prepare file path in storage (videos are stored as video_id.mp4)
        storage_path = f"{video_id}.mp4"
        
        # Read the video file
        with open(video_path, 'rb') as file:
            file_data = file.read()
        
        logger.info(f"Uploading video {video_id} to Supabase Storage...")
        
        # Upload file to Supabase Storage
        response = supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=file_data,
            file_options={
                "content-type": "video/mp4"
            }
        )
        
        # Check if upload was successful
        # The UploadResponse object contains path information if successful
        if response and hasattr(response, 'path'):
            logger.info(f"Video uploaded successfully: {storage_path}")
            
            # Get public URL
            public_url = get_public_url(video_id)
            logger.info(f"Public URL generated: {public_url}")
            return public_url
        else:
            logger.error(f"Upload failed: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to upload video to Supabase: {str(e)}")
        return None


def get_public_url(video_id: str) -> str:
    """
    Get the public URL for a video stored in Supabase Storage.
    
    Args:
        video_id: Unique identifier for the video
        
    Returns:
        Public URL of the video
    """
    try:
        supabase = get_supabase_client()
        bucket_name = get_storage_bucket_name()
        storage_path = f"{video_id}.mp4"
        
        # Get public URL
        response = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        return response
        
    except Exception as e:
        logger.error(f"Failed to get public URL for video {video_id}: {str(e)}")
        # Fallback URL construction (if the above method fails)
        from utils.supabase_config import get_supabase_config
        config = get_supabase_config()
        return f"{config.url}/storage/v1/object/public/{bucket_name}/{video_id}.mp4"


async def delete_video_from_supabase(video_id: str) -> bool:
    """
    Delete a video file from Supabase Storage.
    
    Args:
        video_id: Unique identifier for the video
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        bucket_name = get_storage_bucket_name()
        storage_path = f"{video_id}.mp4"
        
        logger.info(f"Deleting video {video_id} from Supabase Storage...")
        
        response = supabase.storage.from_(bucket_name).remove([storage_path])
        
        if response.data:
            logger.info(f"Video deleted successfully: {storage_path}")
            return True
        else:
            logger.error(f"Deletion failed: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete video from Supabase: {str(e)}")
        return False


async def check_video_exists(video_id: str) -> bool:
    """
    Check if a video exists in Supabase Storage.
    
    Args:
        video_id: Unique identifier for the video
        
    Returns:
        True if video exists, False otherwise
    """
    try:
        supabase = get_supabase_client()
        bucket_name = get_storage_bucket_name()
        storage_path = f"{video_id}.mp4"
        
        # List files in the bucket
        response = supabase.storage.from_(bucket_name).list()
        
        if response:
            # Check if our specific file is in the results
            for file_info in response:
                if file_info.get('name') == storage_path:
                    return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to check if video exists: {str(e)}")
        return False


async def get_video_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a video stored in Supabase Storage.
    
    Args:
        video_id: Unique identifier for the video
        
    Returns:
        Dictionary containing video metadata or None if not found
    """
    try:
        supabase = get_supabase_client()
        bucket_name = get_storage_bucket_name()
        storage_path = f"{video_id}.mp4"
        
        # List files with the specific path to get metadata
        response = supabase.storage.from_(bucket_name).list(
            path="",
            search=storage_path
        )
        
        if response.data:
            for file_info in response.data:
                if file_info.get('name') == storage_path:
                    return {
                        'id': file_info.get('id'),
                        'name': file_info.get('name'),
                        'size': file_info.get('metadata', {}).get('size'),
                        'mimetype': file_info.get('metadata', {}).get('mimetype'),
                        'created_at': file_info.get('created_at'),
                        'updated_at': file_info.get('updated_at')
                    }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get video metadata: {str(e)}")
        return None