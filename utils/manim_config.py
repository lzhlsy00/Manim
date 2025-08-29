#!/usr/bin/env python3
"""
Manim优化配置管理
"""

# Manim渲染质量配置
MANIM_QUALITY_SETTINGS = {
    'l': {  # Low quality (480p)
        'resolution': '480p15',
        'frame_rate': 15,
        'coordinates_scale': 0.8,
        'font_scale': 0.9
    },
    'm': {  # Medium quality (720p) - 默认
        'resolution': '720p30', 
        'frame_rate': 30,
        'coordinates_scale': 1.0,
        'font_scale': 1.0
    },
    'h': {  # High quality (1080p)
        'resolution': '1080p60',
        'frame_rate': 60,
        'coordinates_scale': 1.2,
        'font_scale': 1.1
    },
    'p': {  # Production quality
        'resolution': '1440p60',
        'frame_rate': 60,
        'coordinates_scale': 1.4,
        'font_scale': 1.2
    },
    'k': {  # 4K quality
        'resolution': '2160p60',
        'frame_rate': 60,
        'coordinates_scale': 1.6,
        'font_scale': 1.3
    }
}

# 数学图形优化参数
MATH_OPTIMIZATION_CONFIG = {
    # 基础几何尺寸限制（调大图形基础尺寸）
    'max_triangle_side': 1.5,     # 从1.0增加到1.5
    'max_square_side': 1.4,       # 从1.0增加到1.4
    'max_circle_radius': 1.2,     # 从0.8增加到1.2
    'max_line_length': 2.0,       # 从1.5增加到2.0
    
    # 间距控制
    'min_spacing': 0.3,
    'optimal_spacing': 0.4,
    'safe_spacing': 0.5,
    
    # 布局区域
    'title_zone_y': 2.5,
    'left_zone_x_range': (-6.0, -1.0),
    'right_zone_x_range': (1.0, 6.0),
    'content_zone_y_range': (-2.5, 2.5),
    
    # 字体大小
    'title_font_size': 32,
    'text_font_size': 16,
    'math_font_size': 20,
    
    # 缩放参数（增大整体缩放）
    'graphics_scale': 1.0,        # 从0.7增加到1.0（不缩小）
    'safe_scale': 0.85,           # 从0.6增加到0.85  
    'emergency_scale': 0.7        # 从0.5增加到0.7
}

# 质量检查阈值
QUALITY_THRESHOLDS = {
    'coordinate_limit': 1.5,
    'size_limit': 1.2,
    'spacing_minimum': 0.2,
    'quality_score_minimum': 70,
    'max_retry_attempts': 3
}

def get_quality_config(resolution: str) -> dict:
    """根据分辨率获取质量配置"""
    return MANIM_QUALITY_SETTINGS.get(resolution, MANIM_QUALITY_SETTINGS['m'])

def get_math_config() -> dict:
    """获取数学优化配置"""
    return MATH_OPTIMIZATION_CONFIG

def get_quality_thresholds() -> dict:
    """获取质量检查阈值"""
    return QUALITY_THRESHOLDS
