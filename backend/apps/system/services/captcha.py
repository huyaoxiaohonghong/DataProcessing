"""
滑动验证码服务
Slide Captcha Service
"""
import random
import string
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter
from django.core.cache import cache


class CaptchaService:
    """滑动验证码生成服务"""
    
    # 图片尺寸
    IMAGE_WIDTH = 280
    IMAGE_HEIGHT = 155
    
    # 拼图块尺寸
    PUZZLE_SIZE = 50
    
    # 允许的误差范围（像素）
    TOLERANCE = 5
    
    # 验证码有效期（秒）
    CAPTCHA_EXPIRE = 300  # 5分钟
    
    @staticmethod
    def generate_captcha_key():
        """生成唯一的验证码key"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    @staticmethod
    def create_background():
        """创建背景图"""
        # 创建渐变背景
        image = Image.new('RGB', (CaptchaService.IMAGE_WIDTH, CaptchaService.IMAGE_HEIGHT))
        draw = ImageDraw.Draw(image)
        
        # 随机颜色渐变
        start_color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        end_color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        
        for y in range(CaptchaService.IMAGE_HEIGHT):
            ratio = y / CaptchaService.IMAGE_HEIGHT
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            draw.line([(0, y), (CaptchaService.IMAGE_WIDTH, y)], fill=(r, g, b))
        
        # 添加噪点
        for _ in range(100):
            x = random.randint(0, CaptchaService.IMAGE_WIDTH - 1)
            y = random.randint(0, CaptchaService.IMAGE_HEIGHT - 1)
            draw.point((x, y), fill=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ))
        
        return image
    
    @staticmethod
    def create_puzzle_piece(x, y):
        """创建拼图块路径（带凹凸）"""
        size = CaptchaService.PUZZLE_SIZE
        # 简化版：创建一个带缺口的正方形
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        
        # 绘制主体正方形
        draw.rectangle([0, 0, size-1, size-1], fill=255)
        
        # 在顶部和右侧添加凸起（圆形）
        r = size // 4  # 圆的半径
        
        # 顶部凸起
        draw.ellipse([size//2 - r, -r, size//2 + r, r], fill=255)
        
        # 右侧凸起
        draw.ellipse([size - r, size//2 - r, size + r, size//2 + r], fill=255)
        
        return mask
    
    @staticmethod
    def generate_captcha():
        """生成滑动验证码"""
        # 创建背景图
        bg_image = CaptchaService.create_background()
        
        # 随机生成拼图块位置（确保不太靠边）
        x = random.randint(
            CaptchaService.PUZZLE_SIZE + 20, 
            CaptchaService.IMAGE_WIDTH - CaptchaService.PUZZLE_SIZE - 20
        )
        y = random.randint(
            20, 
            CaptchaService.IMAGE_HEIGHT - CaptchaService.PUZZLE_SIZE - 20
        )
        
        # 创建拼图块遮罩
        puzzle_mask = CaptchaService.create_puzzle_piece(x, y)
        
        # 从背景图中提取拼图块
        puzzle_piece = Image.new('RGBA', (CaptchaService.PUZZLE_SIZE, CaptchaService.PUZZLE_SIZE), (0, 0, 0, 0))
        bg_region = bg_image.crop((x, y, x + CaptchaService.PUZZLE_SIZE, y + CaptchaService.PUZZLE_SIZE))
        
        # 复制背景区域到拼图块
        for i in range(CaptchaService.PUZZLE_SIZE):
            for j in range(CaptchaService.PUZZLE_SIZE):
                if puzzle_mask.getpixel((i, j)) > 0:
                    pixel = bg_region.getpixel((i, j))
                    # 增加拼图块亮度，让它更突出
                    enhanced_pixel = (
                        min(255, pixel[0] + 30),
                        min(255, pixel[1] + 30),
                        min(255, pixel[2] + 30),
                        255
                    )
                    puzzle_piece.putpixel((i, j), enhanced_pixel)
        
        # 给拼图块添加明显的边框
        puzzle_draw = ImageDraw.Draw(puzzle_piece)
        for i in range(CaptchaService.PUZZLE_SIZE):
            for j in range(CaptchaService.PUZZLE_SIZE):
                if puzzle_mask.getpixel((i, j)) > 0:
                    # 检查是否是边界像素
                    is_border = False
                    if i == 0 or j == 0 or i == CaptchaService.PUZZLE_SIZE - 1 or j == CaptchaService.PUZZLE_SIZE - 1:
                        is_border = True
                    elif (i > 0 and puzzle_mask.getpixel((i-1, j)) == 0) or \
                         (i < CaptchaService.PUZZLE_SIZE - 1 and puzzle_mask.getpixel((i+1, j)) == 0) or \
                         (j > 0 and puzzle_mask.getpixel((i, j-1)) == 0) or \
                         (j < CaptchaService.PUZZLE_SIZE - 1 and puzzle_mask.getpixel((i, j+1)) == 0):
                        is_border = True
                    
                    if is_border:
                        # 绘制白色边框
                        puzzle_piece.putpixel((i, j), (255, 255, 255, 255))
        
        # 在背景图上绘制缺口（添加深色阴影效果）
        bg_with_hole = bg_image.copy()
        
        # 先暗化整个缺口区域
        for i in range(CaptchaService.PUZZLE_SIZE):
            for j in range(CaptchaService.PUZZLE_SIZE):
                if puzzle_mask.getpixel((i, j)) > 0:
                    if x + i < CaptchaService.IMAGE_WIDTH and y + j < CaptchaService.IMAGE_HEIGHT:
                        px = bg_with_hole.getpixel((x + i, y + j))
                        # 大幅度暗化，让缺口更明显
                        bg_with_hole.putpixel((x + i, y + j), (
                            max(0, px[0] - 80),
                            max(0, px[1] - 80),
                            max(0, px[2] - 80)
                        ))
        
        # 添加边框（白色高光）
        for i in range(CaptchaService.PUZZLE_SIZE):
            for j in range(CaptchaService.PUZZLE_SIZE):
                if puzzle_mask.getpixel((i, j)) > 0:
                    # 检查是否是边界
                    is_border = False
                    if i == 0 or j == 0 or i == CaptchaService.PUZZLE_SIZE - 1 or j == CaptchaService.PUZZLE_SIZE - 1:
                        is_border = True
                    elif (i > 0 and puzzle_mask.getpixel((i-1, j)) == 0) or \
                         (i < CaptchaService.PUZZLE_SIZE - 1 and puzzle_mask.getpixel((i+1, j)) == 0) or \
                         (j > 0 and puzzle_mask.getpixel((i, j-1)) == 0) or \
                         (j < CaptchaService.PUZZLE_SIZE - 1 and puzzle_mask.getpixel((i, j+1)) == 0):
                        is_border = True
                    
                    if is_border:
                        if x + i < CaptchaService.IMAGE_WIDTH and y + j < CaptchaService.IMAGE_HEIGHT:
                            # 绘制白色边框，让缺口更清晰
                            bg_with_hole.putpixel((x + i, y + j), (255, 255, 255))
        
        # 将图片转为 base64
        bg_buffer = BytesIO()
        bg_with_hole.save(bg_buffer, format='PNG')
        bg_base64 = base64.b64encode(bg_buffer.getvalue()).decode('utf-8')
        
        puzzle_buffer = BytesIO()
        puzzle_piece.save(puzzle_buffer, format='PNG')
        puzzle_base64 = base64.b64encode(puzzle_buffer.getvalue()).decode('utf-8')
        
        # 生成验证码key
        captcha_key = CaptchaService.generate_captcha_key()
        
        # 存储正确的位置到缓存（只存X坐标，Y坐标前端不需要验证）
        cache.set(
            f'captcha:{captcha_key}',
            {'x': x, 'y': y},
            CaptchaService.CAPTCHA_EXPIRE
        )
        
        return {
            'captcha_key': captcha_key,
            'background': f'data:image/png;base64,{bg_base64}',
            'puzzle': f'data:image/png;base64,{puzzle_base64}',
            'y': y  # 告诉前端拼图块的Y坐标
        }
    
    @staticmethod
    def verify_captcha(captcha_key, x_offset):
        """
        验证滑动位置是否正确
        :param captcha_key: 验证码key
        :param x_offset: 用户滑动的X偏移量
        :return: (是否成功, 消息)
        """
        # 从缓存获取正确位置
        captcha_data = cache.get(f'captcha:{captcha_key}')
        
        if not captcha_data:
            return False, '验证码已过期，请重新获取'
        
        correct_x = captcha_data['x']
        
        # 检查误差范围
        if abs(x_offset - correct_x) <= CaptchaService.TOLERANCE:
            # 验证成功后删除缓存（一次性使用）
            cache.delete(f'captcha:{captcha_key}')
            return True, '验证成功'
        else:
            # 验证失败，保留验证码，但可以限制尝试次数
            return False, '验证失败，请重试'
