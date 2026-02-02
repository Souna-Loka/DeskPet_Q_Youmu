import os
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QPainter
from utils.config import Config

class AnimationManager:
    """管理角色动画"""
    
    def __init__(self, character_label, image_path=None, heart_manager=None):
        if image_path is None:
            image_path = Config.get_full_path(Config.IMAGE_PATH)
        else:
            image_path = Config.get_full_path(image_path)
        self.character_label = character_label
        self.image_path = image_path
        self.heart_manager = heart_manager  # 好感度管理器引用
        self.is_speaking = False
        self.current_state = "normal1"
        self.animation_timer = QTimer()
        # 闭眼定时器
        self.animation_timer.timeout.connect(self._change_mouth)
        self.close_eye_timer = QTimer()
        self.close_eye_timer.setSingleShot(True)
        self.close_eye_timer.timeout.connect(self.stop_close_eyes)
                
        # 加载图片
        self._load_all_images()
        
        # 设置标签大小
        if not self.normal1.isNull():
            self.character_label.setFixedSize(
                self.normal1.width(),
                self.normal1.height()
            )
        else:
            # 使用默认大小
            self.character_label.setFixedSize(
                Config.CHARACTER_SIZE, 
                Config.CHARACTER_SIZE
            )
        
        # 设置初始状态
        self._update_display("normal1")
    
    def _load_all_images(self):
        """加载正常和不开心两套图片"""
        # 正常状态图片
        self.normal1 = self._load_image("normal1", Config.IMAGES)
        self.normal2 = self._load_image("normal2", Config.IMAGES)
        self.thinking = self._load_image("normal3", Config.IMAGES)
        self.close_eye = self._load_image("normal4", Config.IMAGES)
        
        # 不开心状态图片（如果文件不存在会返回占位图）
        self.unhappy1 = self._load_image("normal1", Config.UNHAPPY_IMAGES)
        self.unhappy2 = self._load_image("normal2", Config.UNHAPPY_IMAGES)
        self.unhappy3 = self._load_image("normal3", Config.UNHAPPY_IMAGES)
        self.unhappy4 = self._load_image("normal4", Config.UNHAPPY_IMAGES)
    
    def _load_image(self, image_name, image_config=None):
        """加载图片并等比例缩放，支持从不同配置加载"""
        if image_config is None:
            image_config = Config.IMAGES
            
        try:
            image_path = os.path.join(self.image_path, image_config[image_name])
            image = QPixmap(image_path)
            if image.isNull():
                # 创建占位图
                print(f"图片加载失败: {image_path}")
                image = QPixmap(Config.CHARACTER_SIZE, Config.CHARACTER_SIZE)
                image.fill(Qt.transparent)
                painter = QPainter(image)
                painter.setBrush(Qt.blue)
                painter.drawEllipse(0, 0, Config.CHARACTER_SIZE, Config.CHARACTER_SIZE)
                painter.end()
                return image
            
            # 计算缩放后的尺寸
            original_width = image.width()
            original_height = image.height()
            
            scaled_width = int(original_width * Config.SCALE_FACTOR)
            scaled_height = int(original_height * Config.SCALE_FACTOR)
            
            # 等比例缩放
            image = image.scaled(
                scaled_width, 
                scaled_height, 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )        
            return image
        except Exception as e:
            print(f"加载图片异常: {e}")
            # 创建默认图片
            image = QPixmap(Config.CHARACTER_SIZE, Config.CHARACTER_SIZE)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            painter.setBrush(Qt.blue)
            painter.drawEllipse(0, 0, Config.CHARACTER_SIZE, Config.CHARACTER_SIZE)
            painter.end()
            return image
        
    def _is_unhappy(self):
        """判断当前是否应该显示不开心表情"""
        if self.heart_manager is None:
            return False
        return self.heart_manager.score < Config.UNHAPPY_THRESHOLD
    
    def _get_image(self, state):
        """根据当前好感度获取对应状态的图片"""
        is_unhappy = self._is_unhappy()
        
        if state == "normal1":
            return self.unhappy1 if is_unhappy else self.normal1
        elif state == "normal2":
            return self.unhappy2 if is_unhappy else self.normal2
        elif state == "thinking":
            return self.unhappy3 if is_unhappy else self.thinking
        elif state == "close_eye":
            return self.unhappy4 if is_unhappy else self.close_eye
        else:
            return self.normal1
    
    def _update_display(self, state):
        """更新显示"""
        pixmap = self._get_image(state)
        self.character_label.setPixmap(pixmap)
        self.current_state = state
    
    def start_speaking(self):
        """开始说话动画"""
        if not self.is_speaking:
            self.is_speaking = True
            self.animation_timer.start(Config.SPEAKING_INTERVAL)
    
    def stop_speaking(self):
        """停止说话动画"""
        self.is_speaking = False
        self.animation_timer.stop()
        self._update_display("normal1")
    
    def _change_mouth(self):
        """嘴部动画"""
        if self.is_speaking:
            # 在两张图片之间切换
            if self.current_state == "normal1":
                self._update_display("normal2")
            else:
                self._update_display("normal1")

    def set_thinking_state(self):
        """设置思考状态"""
        self.is_speaking = False
        self.animation_timer.stop()
        self._update_display("thinking")

    def close_eyes(self):
        """闭眼动画"""
        # 停止其他动画
        self.is_speaking = False
        self.animation_timer.stop()
        # 显示闭眼图片
        self._update_display("close_eye")
        # 定时恢复
        self.close_eye_timer.start(Config.CLOSE_EYE_DURATION)
    
    def stop_close_eyes(self):
        """停止闭眼，恢复正常状态"""
        if self.close_eye_timer.isActive():
            self.close_eye_timer.stop()
        self._update_display("normal1")