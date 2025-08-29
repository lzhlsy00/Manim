"""
数据库日志处理器 - 实时捕获终端输出并更新到数据库
"""

import logging
import asyncio
from services.database_service import get_database_service

class DatabaseLogHandler(logging.Handler):
    """将日志实时写入数据库status表的处理器"""
    
    def __init__(self, db_uuid: str, prompt: str = None):
        super().__init__()
        self.db_uuid = db_uuid  # videos表的数据库UUID
        self.prompt = prompt  # 用户输入的提示词（带时间戳）
        self.db_service = get_database_service()
        self.step_counter = 1  # 步骤计数器
    
    def emit(self, record):
        """处理日志记录 - 为每个步骤插入一条status记录"""
        try:
            # 过滤掉HTTP客户端日志，避免无限循环
            if record.name in ['httpx', 'urllib3', 'requests', 'supabase']:
                return
            
            # 过滤掉包含HTTP请求信息的日志
            if 'HTTP Request:' in record.getMessage() or 'HTTP/' in record.getMessage():
                return
            
            # 只记录步骤信息到数据库（不包括错误和警告）
            message = record.getMessage()
            is_step = any(keyword in message for keyword in ['步骤', '开始生成', '启动完成'])
            
            if not is_step:
                return  # 只记录步骤信息
            
            # 为当前步骤插入新的status记录
            asyncio.create_task(
                self.db_service.add_step_status(self.db_uuid, self.step_counter, message, self.prompt)
            )
            
            # 递增步骤计数器
            self.step_counter += 1
            
        except Exception as e:
            # 避免日志处理器本身的错误影响主程序
            print(f"数据库日志处理器错误: {e}")

def setup_database_logging(db_uuid: str, prompt: str = None):
    """
    设置数据库日志记录
    Args:
        db_uuid: videos表的数据库UUID
        prompt: 用户输入的提示词（带时间戳）
    Returns:
        日志处理器实例
    """
    handler = DatabaseLogHandler(db_uuid, prompt)
    handler.setLevel(logging.INFO)
    
    # 不需要格式化器，直接使用消息内容
    
    # 添加到根日志器
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    return handler

def remove_database_logging(handler):
    """移除数据库日志处理器"""
    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)
