"""
数据库服务 - 处理videos和status表的操作
"""

import logging
from typing import Optional
from utils.config import load_environment
from utils.supabase_config import get_supabase_client

# 确保环境变量被加载
load_environment()

logger = logging.getLogger(__name__)

class DatabaseService:
    """数据库操作服务类"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_video_record(self, video_id: str, prompt: str = None, user_name: str = None) -> Optional[str]:
        """
        创建视频记录
        Args:
            video_id: 生成的视频ID (存储到video_id字段)
            prompt: 用户输入的提示词
            user_name: 用户名称
        Returns:
            创建成功返回数据库生成的UUID，失败返回None
        """
        try:
            data = {
                'video_id': video_id,  # 生成的视频ID存储到video_id字段
                'video_url': None,
                'user_name': user_name  # 存储用户名
            }
            
            logger.info(f"📝 准备插入视频记录: video_id={video_id}, user_name={user_name}")
            
            # 如果提供了prompt，添加到数据中
            if prompt:
                data['prompt'] = prompt
                
            response = self.supabase.table('videos').insert(data).execute()
            
            if response.data:
                db_uuid = response.data[0]['id']  # 数据库自动生成的UUID
                stored_user_name = response.data[0].get('user_name')
                logger.info(f"✅ 视频记录创建成功: video_id={video_id}, db_id={db_uuid}, 存储的用户名={stored_user_name}")
                return db_uuid
            else:
                logger.error(f"❌ 视频记录创建失败: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建视频记录时出错: {str(e)}")
            return None
    
    async def update_video_url(self, video_id: str, video_url: str) -> bool:
        """
        更新视频URL
        Args:
            video_id: 生成的视频ID (查询video_id字段)
            video_url: 视频URL
        """
        try:
            response = self.supabase.table('videos').update({
                'video_url': video_url
            }).eq('video_id', video_id).execute()  # 根据video_id字段查询
            
            if response.data:
                logger.info(f"✅ 视频URL更新成功: video_id={video_id}")
                return True
            else:
                logger.error(f"❌ 视频URL更新失败: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新视频URL时出错: {str(e)}")
            return False
    
    async def create_status_record(self, db_uuid: str, initial_status: str = "开始生成视频...", step: int = 1, prompt: str = None) -> Optional[str]:
        """
        创建status记录
        Args:
            db_uuid: videos表的数据库UUID (外键)
            initial_status: 初始状态信息
            step: 步骤编号
            prompt: 用户输入的提示词
        Returns:
            创建成功返回status表的UUID，失败返回None
        """
        try:
            data = {
                'video_uuid': db_uuid,  # 外键引用videos表的id
                'build_status': initial_status,
                'step': step
            }
            
            # 如果提供了prompt，添加到数据中
            if prompt:
                data['prompt'] = prompt
                
            response = self.supabase.table('status').insert(data).execute()
            
            if response.data:
                status_uuid = response.data[0]['id']  # status表自动生成的UUID
                logger.info(f"✅ 状态记录创建成功: status_id={status_uuid}")
                return status_uuid
            else:
                logger.error(f"❌ 状态记录创建失败: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建状态记录时出错: {str(e)}")
            return None
    
    async def update_build_status(self, db_uuid: str, status_message: str) -> bool:
        """
        更新构建状态
        Args:
            db_uuid: videos表的数据库UUID
            status_message: 状态消息
        """
        try:
            response = self.supabase.table('status').update({
                'build_status': status_message
            }).eq('video_uuid', db_uuid).execute()  # 根据外键查询
            
            if response.data:
                logger.debug(f"✅ 构建状态更新成功")
                return True
            else:
                logger.error(f"❌ 更新构建状态失败: {response}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新构建状态时出错: {str(e)}")
            return False
    
    async def add_step_status(self, db_uuid: str, step: int, status_message: str, prompt: str = None) -> Optional[str]:
        """
        添加新的步骤状态记录
        Args:
            db_uuid: videos表的数据库UUID
            step: 步骤编号
            status_message: 状态消息
            prompt: 用户输入的提示词
        Returns:
            创建成功返回status表的UUID，失败返回None
        """
        try:
            data = {
                'video_uuid': db_uuid,
                'build_status': status_message,
                'step': step
            }
            
            # 如果提供了prompt，添加到数据中
            if prompt:
                data['prompt'] = prompt
                
            response = self.supabase.table('status').insert(data).execute()
            
            if response.data:
                status_uuid = response.data[0]['id']
                logger.info(f"✅ 步骤 {step} 状态记录创建成功: {status_message}")
                return status_uuid
            else:
                logger.error(f"❌ 步骤状态记录创建失败: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建步骤状态记录时出错: {str(e)}")
            return None
    
    async def get_video_by_video_id(self, video_id: str) -> Optional[dict]:
        """
        根据video_id获取视频记录及其状态
        """
        try:
            response = self.supabase.table('videos').select('*, status(*)').eq('video_id', video_id).execute()
            
            if response.data:
                return response.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取视频记录时出错: {str(e)}")
            return None
    
    async def get_videos_by_user(self, user_name: str) -> list:
        """
        根据用户名获取用户的所有视频
        Args:
            user_name: 用户名称
        Returns:
            用户的视频列表
        """
        try:
            response = self.supabase.table('videos').select('*').eq('user_name', user_name).order('id', desc=True).execute()
            
            return response.data if response.data else []
                
        except Exception as e:
            logger.error(f"❌ 获取用户视频列表时出错: {str(e)}")
            return []

# 全局数据库服务实例
_db_service = None

def get_database_service():
    """获取数据库服务实例"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
