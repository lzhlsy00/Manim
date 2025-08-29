"""Services package for Manimations API."""

from .script_generator import (
    get_anthropic_client,
    generate_and_refine_manim_script,
    fix_manim_script_from_error,
    detect_language,
    estimate_narration_duration
)

from .audio_processor import (
    get_openai_client,
    extract_animation_timing,
    generate_timed_narration,
    create_synchronized_audio,
    extract_narration_from_script,
    generate_tts_audio,
    get_voice_for_language,
    add_subtitles_to_video,
    adjust_audio_duration
)

from .video_processor import (
    execute_manim_script,
    get_video_duration,
    check_ffmpeg_available,
    combine_audio_video
)

__all__ = [
    # Script generation
    "get_anthropic_client",
    "generate_and_refine_manim_script", 
    "fix_manim_script_from_error",
    "detect_language",
    "estimate_narration_duration",
    
    # Audio processing
    "get_openai_client",
    "extract_animation_timing",
    "generate_timed_narration",
    "create_synchronized_audio",
    "extract_narration_from_script",
    "generate_tts_audio",
    "get_voice_for_language",
    "add_subtitles_to_video",
    "adjust_audio_duration",
    
    # Video processing
    "execute_manim_script",
    "get_video_duration",
    "check_ffmpeg_available",
    "combine_audio_video"
]