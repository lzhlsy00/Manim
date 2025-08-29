#!/usr/bin/env python3
"""
Manim视频质量优化器
专门优化数学图形的显示精度，防止错位重叠等问题
"""

import re
import ast
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ManimOptimizer:
    """Manim脚本优化器，提升数学图形质量"""
    
    def __init__(self):
        # 定义安全的坐标范围
        self.safe_bounds = {
            'title_zone': {'y_min': 2.5, 'y_max': 4.0},
            'left_zone': {'x_min': -6.0, 'x_max': -1.0, 'y_min': -2.5, 'y_max': 2.5},
            'right_zone': {'x_min': 1.0, 'x_max': 6.0, 'y_min': -2.5, 'y_max': 2.5},
            'buffer_zone': {'x_min': -1.0, 'x_max': 1.0}
        }
        
        # 数学图形的最佳尺寸参数（增大图形尺寸）
        self.optimal_sizes = {
            'triangle_max_side': 1.8,     # 从1.2增加到1.8
            'square_max_side': 1.6,       # 从1.0增加到1.6
            'circle_max_radius': 1.3,     # 从0.8增加到1.3
            'line_max_length': 2.2,       # 从1.5增加到2.2
            'text_font_size': 16,
            'title_font_size': 32,
            'min_spacing': 0.3,
            'optimal_spacing': 0.4
        }
    
    def optimize_script(self, script: str) -> str:
        """
        全面优化Manim脚本
        """
        logger.info("开始优化Manim脚本...")
        
        # 1. 修复坐标超限问题
        script = self._fix_coordinate_bounds(script)
        
        # 2. 优化图形尺寸
        script = self._optimize_geometry_sizes(script)
        
        # 3. 增强间距控制
        script = self._enhance_spacing_control(script)
        
        # 4. 添加精确定位
        script = self._add_precise_positioning(script)
        
        # 5. 优化数学公式渲染
        script = self._optimize_math_rendering(script)
        
        # 6. 添加边界检查
        script = self._add_boundary_validation(script)
        
        logger.info("Manim脚本优化完成")
        return script
    
    def _fix_coordinate_bounds(self, script: str) -> str:
        """修复坐标超出安全范围的问题"""
        
        # 更精确的坐标修复规则（放宽限制以允许更大图形）
        coordinate_patterns = {
            # 右侧图形区域的坐标限制（增大允许范围）
            r'(\d+(?:\.\d+)?)\s*\*\s*RIGHT': lambda m: f"{min(1.8, float(m.group(1)))}*RIGHT" if float(m.group(1)) > 1.8 else m.group(0),
            r'(\d+(?:\.\d+)?)\s*\*\s*UP': lambda m: f"{min(2.0, float(m.group(1)))}*UP" if float(m.group(1)) > 2.0 else m.group(0),
            r'(\d+(?:\.\d+)?)\s*\*\s*DOWN': lambda m: f"{min(2.0, float(m.group(1)))}*DOWN" if float(m.group(1)) > 2.0 else m.group(0),
            r'(\d+(?:\.\d+)?)\s*\*\s*LEFT': lambda m: f"{min(1.8, float(m.group(1)))}*LEFT" if float(m.group(1)) > 1.8 else m.group(0),
            
            # 尺寸参数限制（允许更大尺寸）
            r'side_length\s*=\s*(\d+(?:\.\d+)?)': lambda m: f"side_length={min(1.6, float(m.group(1)))}" if float(m.group(1)) > 1.6 else m.group(0),
            r'radius\s*=\s*(\d+(?:\.\d+)?)': lambda m: f"radius={min(1.3, float(m.group(1)))}" if float(m.group(1)) > 1.3 else m.group(0),
        }
        
        for pattern, replacement in coordinate_patterns.items():
            script = re.sub(pattern, replacement, script)
        
        return script
    
    def _optimize_geometry_sizes(self, script: str) -> str:
        """优化几何图形的尺寸以确保最佳显示效果"""
        
        # 三角形优化
        triangle_pattern = r'Polygon\s*\(\s*ORIGIN\s*,\s*([^,]+)\s*,\s*([^)]+)\)'
        def optimize_triangle(match):
            point1 = match.group(1).strip()
            point2 = match.group(2).strip()
            
            # 确保三角形不会太大
            if '*RIGHT' in point1 and '*UP' in point2:
                return f'Polygon(ORIGIN, 1.0*RIGHT, 1.0*RIGHT + 1.2*UP)'
            return match.group(0)
        
        script = re.sub(triangle_pattern, optimize_triangle, script)
        
        # 正方形优化（使用更大的默认尺寸）
        script = re.sub(
            r'Square\s*\(\s*side_length\s*=\s*\d+(?:\.\d+)?\s*\)',
            'Square(side_length=1.4)',  # 从1.0增加到1.4
            script
        )
        
        # 圆形优化（使用更大的默认半径）
        script = re.sub(
            r'Circle\s*\(\s*radius\s*=\s*\d+(?:\.\d+)?\s*\)',
            'Circle(radius=1.1)',  # 从0.8增加到1.1
            script
        )
        
        return script
    
    def _enhance_spacing_control(self, script: str) -> str:
        """增强间距控制，确保元素不重叠"""
        
        # 强制使用合适的间距
        spacing_patterns = {
            r'\.arrange\s*\(\s*DOWN\s*\)': '.arrange(DOWN, buff=0.4)',
            r'\.arrange\s*\(\s*RIGHT\s*\)': '.arrange(RIGHT, buff=0.4)',
            r'\.arrange\s*\(\s*UP\s*\)': '.arrange(UP, buff=0.4)',
            r'\.arrange\s*\(\s*LEFT\s*\)': '.arrange(LEFT, buff=0.4)',
            r'\.next_to\s*\([^,]+,\s*[^,]+\s*\)': lambda m: m.group(0).replace(')', ', buff=0.3)'),
        }
        
        for pattern, replacement in spacing_patterns.items():
            if callable(replacement):
                script = re.sub(pattern, replacement, script)
            else:
                script = re.sub(pattern, replacement, script)
        
        return script
    
    def _add_precise_positioning(self, script: str) -> str:
        """添加精确的定位控制"""
        
        # 确保所有图形都在正确的区域
        positioning_fixes = []
        
        # 检查是否有图形需要移动到右侧区域
        if re.search(r'(Polygon|Square|Circle|Rectangle)\s*\([^)]*\)', script):
            if 'move_to(RIGHT*3)' not in script:
                # 在construct方法中添加图形分组和定位
                construct_pattern = r'(def construct\(self\):.*?)(self\.play)'
                def add_positioning(match):
                    construct_content = match.group(1)
                    play_start = match.group(2)
                    
                    # 添加图形分组和定位代码
                    positioning_code = '''
        
        # 自动图形分组和定位优化
        all_graphics = []
        for obj_name in dir():
            obj = locals().get(obj_name)
            if hasattr(obj, 'get_center') and obj_name not in ['title', 'text1', 'text2', 'text3', 'text4', 'text5']:
                all_graphics.append(obj)
        
        if all_graphics:
            graphics_group = VGroup(*all_graphics)
            graphics_group.arrange(DOWN, buff=0.4)
            graphics_group.move_to(RIGHT*3)
            graphics_group.scale(1.0)  # 从0.7改为1.0，不缩小
        
        '''
                    return construct_content + positioning_code + play_start
                
                script = re.sub(construct_pattern, add_positioning, script, flags=re.DOTALL)
        
        return script
    
    def _optimize_math_rendering(self, script: str) -> str:
        """优化数学公式的渲染质量"""
        
        # 确保数学公式使用正确的对象类型
        math_optimizations = {
            # 避免中文字符在MathTex中使用
            r'MathTex\s*\(\s*["\']([^"\']*[\u4e00-\u9fff][^"\']*)["\']': lambda m: f'Text("{m.group(1)}", font_size=20)',
            
            # 优化数学公式的字体大小
            r'MathTex\s*\(\s*([^)]+)\s*\)(?!\s*,\s*font_size)': r'MathTex(\1, font_size=24)',
        }
        
        for pattern, replacement in math_optimizations.items():
            if callable(replacement):
                script = re.sub(pattern, replacement, script)
            else:
                script = re.sub(pattern, replacement, script)
        
        return script
    
    def _add_boundary_validation(self, script: str) -> str:
        """添加边界验证代码以防止元素超出屏幕"""
        
        # 在construct方法末尾添加边界检查
        validation_code = '''
        
        # 边界验证和自动调整
        def validate_and_adjust_positions(scene_objects):
            for obj in scene_objects:
                if hasattr(obj, 'get_center'):
                    center = obj.get_center()
                    # 检查是否超出安全边界
                    if center[0] > 5.5:  # 右边界
                        obj.shift(LEFT * (center[0] - 5.0))
                    elif center[0] < -5.5:  # 左边界
                        obj.shift(RIGHT * (-5.0 - center[0]))
                    
                    if center[1] > 3.5:  # 上边界
                        obj.shift(DOWN * (center[1] - 3.0))
                    elif center[1] < -3.5:  # 下边界
                        obj.shift(UP * (-3.0 - center[1]))
        
        # 在动画开始前验证所有对象的位置
        all_scene_objects = [obj for obj in locals().values() if hasattr(obj, 'get_center')]
        validate_and_adjust_positions(all_scene_objects)
        '''
        
        # 将验证代码插入到第一个self.play之前
        script = re.sub(
            r'(\s+)(self\.play)',
            r'\1' + validation_code + r'\n\1\2',
            script,
            count=1
        )
        
        return script
    
    def generate_enhanced_system_prompt(self) -> str:
        """生成增强的系统提示词，包含更严格的质量控制"""
        
        return f"""
        
=== ENHANCED MANIM QUALITY CONTROL ===

CRITICAL MATHEMATICAL ACCURACY RULES:

1. PRECISE COORDINATE CONTROL:
   - Triangle vertices: NEVER exceed 1.0 unit in any direction
   - Square side_length: MAXIMUM 1.0 units
   - Circle radius: MAXIMUM 0.8 units
   - ALL graphics must fit within RIGHT zone: (1 < x < 6, -2.5 < y < 2.5)

2. ANTI-OVERLAP SYSTEM:
   - MANDATORY: Use VGroup().arrange(DOWN, buff=0.4) for vertical stacking
   - MANDATORY: Use VGroup().arrange(RIGHT, buff=0.4) for horizontal alignment
   - NEVER place objects at same coordinates without spacing
   - Use .next_to() with buff=0.3 minimum for adjacent elements

3. MATHEMATICAL PRECISION:
   - For right triangles: Polygon(ORIGIN, 1.0*RIGHT, 1.0*RIGHT + 1.2*UP)
   - For squares on triangle sides: match the exact side lengths
   - For Pythagorean theorem: a=1.0, b=1.2, c=√(1.0²+1.2²)=1.56
   - Use numpy for precise calculations: import numpy as np

4. POSITIONING ACCURACY:
   - ALWAYS use .move_to(RIGHT*3) for graphics group
   - ALWAYS use .scale(0.7) after positioning
   - NEVER use ORIGIN for final positioning
   - Check bounds: graphics.get_center() should be around (3, 0)

5. ENHANCED SPACING FORMULA:
   ```python
   # Correct spacing pattern
   shape1 = Circle(radius=0.6)
   shape2 = Square(side_length=0.8) 
   shape3 = Polygon(ORIGIN, 0.8*RIGHT, 0.8*RIGHT + 1.0*UP)
   
   graphics = VGroup(shape1, shape2, shape3)
   graphics.arrange(DOWN, buff=0.4)  # Prevent overlap
   graphics.move_to(RIGHT*3)         # Right zone
   graphics.scale(0.7)               # Safe scaling
   ```

6. QUALITY VALIDATION:
   - Before animations: verify no overlaps
   - Check all coordinates are within bounds
   - Ensure mathematical relationships are accurate
   - Test visual clarity and readability

RETURN ONLY mathematically precise, visually clear Python code.
        """

def enhance_script_generation_prompt(original_prompt: str) -> str:
    """增强脚本生成的提示词，加入质量控制"""
    
    optimizer = ManimOptimizer()
    enhanced_section = optimizer.generate_enhanced_system_prompt()
    
    # 将增强的质量控制规则添加到原始提示词中
    enhanced_prompt = original_prompt + enhanced_section
    
    return enhanced_prompt

def validate_manim_quality(script: str) -> Dict[str, Any]:
    """验证Manim脚本的质量"""
    
    issues = []
    
    # 检查坐标超限
    large_coords = re.findall(r'(\d+(?:\.\d+)?)\s*\*\s*(?:RIGHT|UP|DOWN|LEFT)', script)
    for coord in large_coords:
        if float(coord) > 1.5:
            issues.append(f"坐标过大: {coord} (建议 ≤1.0)")
    
    # 检查间距设置
    if '.arrange(' in script and 'buff=' not in script:
        issues.append("缺少间距设置，可能导致重叠")
    
    # 检查定位
    if ('Polygon(' in script or 'Square(' in script) and 'move_to(RIGHT*3)' not in script:
        issues.append("图形未正确定位到右侧区域")
    
    # 检查尺寸
    side_lengths = re.findall(r'side_length\s*=\s*(\d+(?:\.\d+)?)', script)
    for size in side_lengths:
        if float(size) > 1.2:
            issues.append(f"图形尺寸过大: {size} (建议 ≤1.0)")
    
    return {
        'has_issues': len(issues) > 0,
        'issues': issues,
        'score': max(0, 100 - len(issues) * 20)  # 质量评分
    }
