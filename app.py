"""
FastAPI application for Manim-based educational animation generation.
Updated to return video_id immediately and process generation in background.
"""

import os
import asyncio
import shutil
import time
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import our models
from models import AnimationRequest, AnimationResponse

# Import auth middleware
from middleware.auth import get_current_user, optional_auth

# Import our services
from services import (
    get_anthropic_client,
    generate_and_refine_manim_script,
    fix_manim_script_from_error,
    detect_language,
    estimate_narration_duration,
    execute_manim_script,
    get_video_duration,
    combine_audio_video,
    extract_animation_timing,
    generate_timed_narration,
    create_synchronized_audio,
    extract_narration_from_script,
    generate_tts_audio,
    add_subtitles_to_video,
    adjust_audio_duration
)
from services.supabase_storage import upload_video_to_supabase
from services.audio_processor import get_audio_duration
from services.database_service import get_database_service
# from utils.database_logger import setup_database_logging, remove_database_logging  # 已禁用

# Import our utilities
from utils import (
    generate_animation_id,
    cleanup_temp_files,
    log_performance,
    validate_prompt
)

# Configure logging
import sys
from datetime import datetime

# 创建过滤后的彩色终端处理器
class FilteredColorHandler(logging.StreamHandler):
    """过滤后的彩色日志处理器 - 只显示步骤、错误和警告"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def emit(self, record):
        try:
            # 只显示步骤、错误和警告信息
            message = record.getMessage()
            
            # 检查是否是需要显示的消息类型
            is_step = any(keyword in message for keyword in ['步骤', '开始生成', '启动完成', '服务地址'])
            is_auth = any(keyword in message for keyword in ['Auth header', 'Current user', '认证用户', '提取到用户名', 'Authorization header', 'Optional auth'])
            is_error = record.levelname in ['ERROR', 'CRITICAL']
            is_warning = record.levelname == 'WARNING'
            
            if not (is_step or is_auth or is_error or is_warning):
                return  # 跳过其他日志
            
            # 添加时间戳
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # 获取颜色
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # 格式化日志消息
            if record.levelname == 'INFO' and is_step:
                # 特殊处理步骤信息
                if '开始生成' in message:
                    emoji = '🚀'
                elif '步骤' in message:
                    emoji = '📝'
                elif '启动完成' in message:
                    emoji = '🚀'
                elif '服务地址' in message:
                    emoji = '🌐'
                else:
                    emoji = '📝'
                
                formatted = f"{color}[{timestamp}] {emoji} {message}{reset}"
            elif is_error:
                formatted = f"{color}[{timestamp}] ❌ {message}{reset}"
            elif is_warning:
                formatted = f"{color}[{timestamp}] ⚠️ {message}{reset}"
            else:
                formatted = f"{color}[{timestamp}] {record.levelname}: {message}{reset}"
            
            # 输出到控制台
            self.stream.write(formatted + '\n')
            self.stream.flush()
            
        except Exception:
            self.handleError(record)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 清除现有的处理器
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 创建控制台处理器
console_handler = FilteredColorHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 添加处理器到根日志记录器
root_logger.addHandler(console_handler)

# 设置HTTP客户端日志级别为WARNING，避免大量HTTP请求日志
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING) 
logging.getLogger('requests').setLevel(logging.WARNING)

# 创建应用特定的日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 添加启动日志
logger.info("🚀 Manim API 启动完成")
logger.info("🌐 服务地址: http://0.0.0.0:8000")

# Create FastAPI app
app = FastAPI(
    title="Manim Educational Animation API",
    description="Generate educational animations using Manim",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("generated_videos", exist_ok=True)
app.mount("/generated_videos", StaticFiles(directory="generated_videos"), name="generated_videos")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "manimations-api"}


@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.post("/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verify if the user is authenticated."""
    return {"authenticated": True, "user": current_user}


@app.post("/generate", response_model=AnimationResponse)
async def generate_animation(
    request: AnimationRequest,
    fastapi_request: Request,
    current_user: dict = Depends(optional_auth)  # Optional auth for development
):
    """
    Generate an educational animation based on the provided prompt.
    Now returns immediately with video_id and processes generation in background.
    """
    # Debug logging
    auth_header = fastapi_request.headers.get("authorization")
    logger.info(f"Generate endpoint called. Auth header: {auth_header[:50] if auth_header else 'None'}...")
    logger.info(f"Current user: {current_user}")
    logger.info(f"Current user type: {type(current_user)}")
    if current_user:
        logger.info(f"User keys: {list(current_user.keys())}")
        logger.info(f"User email: {current_user.get('email')}")
        logger.info(f"User ID: {current_user.get('user_id')}")
    
    animation_id = generate_animation_id()
    
    user_info = current_user.get('email', current_user.get('user_id')) if current_user else 'anonymous'
    logger.info(f"🎬 开始生成视频: {animation_id} - 用户: {user_info}")
    
    # 获取数据库服务
    db_service = get_database_service()
    
    try:
        # 创建带时间戳的prompt信息
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamped_prompt = f"[{current_time}] {request.prompt}"
        
        # 提取用户名用于存储
        user_name = None
        if current_user:
            user_name = current_user.get('email', current_user.get('user_id'))
            logger.info(f"✅ 提取到用户名: {user_name}")
        else:
            logger.warning("⚠️ 当前用户为空，无法提取用户名")
        
        # 1. 创建视频记录（生成的视频ID存储到video_id字段）
        db_uuid = await db_service.create_video_record(animation_id, timestamped_prompt, user_name)
        if db_uuid:
            # 2. 创建status记录并开始记录状态
            await db_service.create_status_record(db_uuid, "🚀 开始生成视频", step=1, prompt=timestamped_prompt)
        else:
            logger.warning("❌ 创建数据库记录失败")
            raise HTTPException(status_code=500, detail="Failed to initialize video generation")
    except Exception as db_error:
        logger.error(f"❌ 数据库初始化失败: {db_error}")
        raise HTTPException(status_code=500, detail="Failed to initialize video generation")
    
    # Validate prompt
    if not validate_prompt(request.prompt):
        await db_service.update_build_status(db_uuid, "❌ 提示词验证失败")
        raise HTTPException(status_code=400, detail="Invalid or unsafe prompt provided")
    
    # Start background video generation task
    asyncio.create_task(generate_video_background(request, animation_id, db_uuid, timestamped_prompt))
    
    # Return immediately with video_id
    return AnimationResponse(
        video_id=animation_id,
        video_url="",  # Will be set when generation completes
        status="processing",
        message="Video generation started successfully"
    )


async def generate_video_background(request: AnimationRequest, animation_id: str, db_uuid: str, prompt: str):
    """
    Background task to generate the video.
    """
    start_time = time.time()
    db_service = get_database_service()
    db_handler = None
    
    try:
        # 不再需要实时日志记录，只记录关键状态点
        db_handler = None
        
        # Step 2: Generate and refine Manim script using Claude
        logger.info("📝 步骤2: 生成Manim脚本")
        await db_service.add_step_status(db_uuid, 2, "📝 开始生成脚本", prompt)
        
        client = get_anthropic_client()
        
        # Detect language from prompt first
        detected_language = request.language or await detect_language(client, request.prompt)
        
        # Estimate target duration for better sync
        if request.include_audio:
            target_duration = await estimate_narration_duration(client, request.prompt)
        else:
            target_duration = 45.0  # Default for videos without audio
        
        manim_script = await generate_and_refine_manim_script(
            client, request.prompt, max_attempts=3, target_duration=target_duration, language=detected_language
        )
        logger.info("✅ 脚本生成完成")
        
        
        # Step 3: Save the generated script
        script_path = f"temp_scripts/{animation_id}.py"
        os.makedirs("temp_scripts", exist_ok=True)
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(manim_script)
        
        # Step 3: Execute the Manim script
        logger.info("🎬 步骤3: 生成动画视频")
        await db_service.add_step_status(db_uuid, 3, "🎬 开始生成动画", prompt)
        
        try:
            video_path = await execute_manim_script(script_path, animation_id, request.resolution)
            logger.info("✅ 动画视频生成完成")
            
        except Exception as manim_error:
            logger.error(f"❌ Manim执行失败: {str(manim_error)}")
            # Try to regenerate script with error feedback
            logger.info("🔧 尝试修复脚本错误...")
            
            client = get_anthropic_client()
            fixed_script = await fix_manim_script_from_error(client, manim_script, str(manim_error), detected_language)
            
            # Save fixed script
            with open(script_path, "w", encoding='utf-8') as f:
                f.write(fixed_script)
            
            # Retry execution
            video_path = await execute_manim_script(script_path, animation_id, request.resolution)
            logger.info("✅ 修复后脚本执行成功")
        
        # Step 4: Generate audio if requested
        final_video_path = f"generated_videos/{animation_id}.mp4"
        if request.include_audio:
            logger.info("🎵 步骤4: 生成音频")
            await db_service.add_step_status(db_uuid, 4, "🎵 开始生成音频", prompt)
            
            # Language was already detected earlier
            
            # Get video duration for timing
            video_duration = await get_video_duration(video_path)
            
            # Handle different sync methods
            if request.sync_method == "timing_analysis":
                # Extract timing information from Manim script
                timing_segments = await extract_animation_timing(client, manim_script)
                
                # Generate synchronized narration
                narration_segments = await generate_timed_narration(
                    client, manim_script, request.prompt, detected_language, timing_segments
                )
                
                # Create synchronized audio
                audio_path = await create_synchronized_audio(
                    narration_segments, animation_id, request.voice, detected_language
                )
                
            elif request.sync_method == "subtitle_overlay":
                narration_text = await extract_narration_from_script(
                    client, manim_script, request.prompt, detected_language, video_duration
                )
                audio_path = await generate_tts_audio(
                    narration_text, animation_id, request.voice, detected_language
                )
                # Add subtitles to video
                final_video_path = await add_subtitles_to_video(
                    video_path, narration_text, final_video_path, detected_language
                )
            else:  # Default fallback - improved simple method
                narration_text = await extract_narration_from_script(
                    client, manim_script, request.prompt, detected_language, video_duration
                )
                audio_path = await generate_tts_audio(
                    narration_text, animation_id, request.voice, detected_language
                )
                # Ensure audio duration matches video by padding or trimming
                audio_duration = await get_audio_duration(audio_path)
                
                if abs(audio_duration - video_duration) > 2.0:  # Significant difference
                    adjusted_audio_path = f"temp_output/{animation_id}_adjusted_audio.mp3"
                    os.makedirs("temp_output", exist_ok=True)
                    await adjust_audio_duration(audio_path, adjusted_audio_path, video_duration)
                    os.remove(audio_path)
                    audio_path = adjusted_audio_path
            
            if request.sync_method != "subtitle_overlay":
                logger.info("🎬 步骤5: 合成音视频")
                
                await combine_audio_video(video_path, audio_path, final_video_path, video_duration)
                logger.info("✅ 音视频合成完成")
                
                
                # Clean up temporary audio
                os.remove(audio_path)
            else:
                # Add subtitles to video if using subtitle overlay
                await add_subtitles_to_video(video_path, narration_text, final_video_path, detected_language)
        else:
            # Step 4: Move video to served directory (no audio)
            shutil.move(video_path, final_video_path)
        
        # 最后步骤：Upload video to Supabase Storage and generate public URL
        final_step = 6 if request.include_audio and request.sync_method != "subtitle_overlay" else 5
        logger.info(f"☁️ 步骤{final_step}: 上传视频")
        
        
        video_url = await upload_video_to_supabase(final_video_path, animation_id)
        
        if not video_url:
            logger.error("❌ 上传视频失败")
            raise Exception("Failed to upload video to storage")
        
        logger.info("✅ 视频上传完成")
        
        # 更新数据库中的视频URL
        try:
            await db_service.update_video_url(animation_id, video_url)
            await db_service.add_step_status(db_uuid, 5, "🎉 完成", prompt)
        except Exception as db_error:
            logger.warning(f"⚠️ 更新数据库失败: {db_error}")
        
        # 数据库日志处理器已禁用，无需移除
        
        # Clean up local video file after successful upload
        try:
            os.remove(final_video_path)
        except Exception as e:
            logger.warning(f"⚠️ 无法清理本地视频文件: {str(e)}")
        
        # Clean up temp script
        os.remove(script_path)
        
        # Log performance
        end_time = time.time()
        total_time = end_time - start_time
        log_performance("generate_animation", start_time, end_time)
        
        logger.info(f"🎉 视频生成完成! 耗时: {total_time:.1f}秒")
        
    except Exception as e:
        # 更新错误状态到数据库
        logger.error(f"❌ 视频生成失败: {str(e)}")
        try:
            await db_service.update_build_status(db_uuid, f"❌ 生成失败：{str(e)}")
        except Exception as db_error:
            logger.warning(f"⚠️ 无法更新数据库中的错误状态: {db_error}")
        
        # 数据库日志处理器已禁用，无需移除
        
        # Clean up any partial files
        cleanup_temp_files(animation_id)


@app.get("/video/{video_id}/status")
async def get_video_status(video_id: str):
    """获取视频生成状态"""
    try:
        db_service = get_database_service()
        video_with_status = await db_service.get_video_by_video_id(video_id)
        
        if not video_with_status:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {
            "video_id": video_id,
            "database_id": video_with_status["id"],
            "video_url": video_with_status["video_url"],
            "status": video_with_status.get("status", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video status: {str(e)}")


@app.get("/videos")
async def list_all_videos():
    """获取所有视频列表"""
    try:
        db_service = get_database_service()
        supabase = db_service.supabase
        response = supabase.table('videos').select('*').order('id', desc=True).execute()
        
        return {
            "videos": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")


@app.get("/videos/user/{user_name}")
async def list_user_videos(user_name: str):
    """获取指定用户的视频列表"""
    try:
        db_service = get_database_service()
        videos = await db_service.get_videos_by_user(user_name)
        
        return {
            "videos": videos,
            "count": len(videos),
            "user_name": user_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list user videos: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # 打印启动信息
    print("🚀 Manim API 启动中...")
    print("🌐 服务地址: http://0.0.0.0:8000")
    print("🔧 HTTP版本: 1.1 (兼容ngrok代理)")
    print("=" * 40)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        http="h11",  # 强制使用HTTP/1.1
        proxy_headers=True,  # 支持代理头
        forwarded_allow_ips="*"  # 允许所有代理IP
    )
