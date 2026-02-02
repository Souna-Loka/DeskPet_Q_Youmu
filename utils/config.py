import os
import sys

class Config:
    """配置类"""
    # 记忆系统配置
    MAX_HISTORY_MESSAGES = 20  # 短期记忆最大条数
    LONG_TERM_MEMORY_LIMIT = 20  # 长期记忆最大条数
    COMPRESSED_MEMORY_RANGE = (5, 10)  # 压缩后的长期记忆保留范围
    MAX_MEMORY_LENGTH = 15  # 单条记忆最大字数
    
    if getattr(sys, 'frozen', False):
        BASE_PATH = os.path.dirname(os.path.abspath(sys.executable))
        external_image = os.path.join(BASE_PATH, "image")
        RESOURCE_PATH = sys._MEIPASS
    else:
        _current_file = os.path.abspath(__file__)
        _utils_dir = os.path.dirname(_current_file)
        BASE_PATH = os.path.dirname(_utils_dir)
        RESOURCE_PATH = BASE_PATH
    
    IMAGE_PATH = os.path.join(RESOURCE_PATH, "image")
    CHARACTER_FILE = os.path.join(BASE_PATH, "txt", "character.json")
    USER_INFO_FILE = os.path.join(BASE_PATH, "txt", "user_info.json")
    SETTING_FILE = os.path.join(BASE_PATH, "txt", "setting.json")
    HISTORY_FILE = os.path.join(BASE_PATH, "log", "talk_log.json")
    
    @classmethod
    def get_full_path(cls, relative_path):
        """获取完整路径"""
        if os.path.isabs(relative_path):
            return relative_path
        
        if relative_path.startswith('image/') or relative_path.startswith('image\\'):
            return os.path.join(cls.RESOURCE_PATH, relative_path)
        else:
            return os.path.join(cls.BASE_PATH, relative_path)
    
    # 图片文件
    IMAGES = {
        "normal1": "normal1.png",
        "normal2": "normal2.png",
        "normal3": "normal3.png",
        "normal4": "normal4.png",
    }

    # 不开心状态图片
    UNHAPPY_IMAGES = {
        "normal1": "unhappy1.png",
        "normal2": "unhappy2.png",
        "normal3": "unhappy3.png",
        "normal4": "unhappy4.png",
    }
    
    # 好感度阈值配置
    UNHAPPY_THRESHOLD = -20
    
    # 窗口设置
    WINDOW_WIDTH = 320
    WINDOW_HEIGHT = 420
    CHARACTER_SIZE = 200
    INPUT_HEIGHT = 20
    
    # 图片缩放设置
    SCALE_FACTOR = 0.15
    
    # 动画设置
    SPEAKING_INTERVAL = 100
    TYPING_SPEED = 50
    SENTENCE_DELAY = 2000
    FINAL_DELAY = 3000
    CLOSE_EYE_DURATION = 500

    # 字体设置
    FONT_FAMILY = "Microsoft YaHei"
    HISTORY_FONT_SIZE = 9
    HISTORY_HEADER_FONT_SIZE = 10
    HISTORY_BUTTON_FONT_SIZE = 10
    
    # UI交互设置
    HIDE_INPUT_DELAY = 500