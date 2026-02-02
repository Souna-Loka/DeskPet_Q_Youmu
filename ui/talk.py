from threading import Thread
from PyQt5.QtCore import Qt, QTimer, QMetaObject, Q_ARG, QObject
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QLabel
from core.heart import HeartManager

class SpeechBubble(QLabel):
    """自定义对话气泡控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(250)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Microsoft YaHei", 10))
        
        # 主题颜色
        self.bg_color = QColor(255, 255, 255, 230)
        self.border_color = QColor(140, 191, 117)
        self.text_color = QColor(46, 47, 42)
        
        # 逐字显示相关
        self.full_text = ""
        self.current_text = ""
        self.char_index = 0
        self.char_delay = 50
        self.type_timer = QTimer(self)
        self.type_timer.timeout.connect(self._type_next_char)
        
        # 分段显示相关
        self.paragraphs = []  # 存储分割后的段落
        self.current_paragraph_index = 0  # 当前段落索引
        
        # 完成停留定时器
        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.hide)
        
        # 位置跟随定时器
        self.follow_timer = QTimer(self)
        self.follow_timer.timeout.connect(self.adjust_position)
        self.follow_timer.start(50)
        
        # 箭头属性
        self.arrow_size = 10
        self.arrow_direction = "top"
        
        # 父窗口引用
        self.parent_window = None
        self.animation_manager = None
        
        self.hide()

    def set_parent_window(self, parent_window):
        """设置父窗口引用"""
        self.parent_window = parent_window

    def set_arrow_direction(self, direction):
        """设置箭头方向"""
        self.arrow_direction = direction
        self.update()

    def setText(self, text):
        """逐字显示"""
        # 按换行分割文本，过滤空段落但保留格式
        self.paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        self.current_paragraph_index = 0
        
        if not self.paragraphs:
            return
        
        # 开始显示第一段
        self._start_paragraph()

    def _start_paragraph(self):
        """开始显示当前段落"""
        if self.current_paragraph_index >= len(self.paragraphs):
            # 所有段落显示完毕，开始最终等待
            self.wait_timer.start(3000)
            return
        
        # 获取当前段落文本
        self.full_text = self.paragraphs[self.current_paragraph_index]
        self.current_text = ""
        self.char_index = 0
        
        # 根据当前段落调整气泡大小
        self.adjust_size(self.full_text)
        self.show()
        self.raise_()
        self.adjust_position()
        
        # 开始说话动画
        if self.animation_manager:
            self.animation_manager.start_speaking()
        
        # 启动逐字显示定时器
        self.type_timer.start(self.char_delay)

    def _type_next_char(self):
        """显示下一个字符"""
        if self.char_index < len(self.full_text):
            self.current_text += self.full_text[self.char_index]
            self.char_index += 1
            super().setText(self.current_text)
            self.update()
        else:
            # 当前段落显示完毕
            self.type_timer.stop()
            
            if self.animation_manager:
                self.animation_manager.stop_speaking()
            
            # 准备显示下一段
            self.current_paragraph_index += 1
            
            if self.current_paragraph_index < len(self.paragraphs):
                # 段落间停顿1.5秒，然后显示下一段
                QTimer.singleShot(1500, self._start_paragraph)
            else:
                # 所有段落显示完毕，停留3秒后隐藏
                self.wait_timer.start(3000)

    def paintEvent(self, event):
        """自定义绘制气泡和箭头"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        rect = self.rect().adjusted(1, 1, -1, -1)
        
        if self.arrow_direction == "top":
            rect.adjust(0, self.arrow_size, 0, 0)
        elif self.arrow_direction == "bottom":
            rect.adjust(0, 0, 0, -self.arrow_size)

        path.addRoundedRect(QRectF(rect), 15, 15)
        path.addPath(self._get_arrow_path(rect))
        
        painter.setPen(self.border_color)
        painter.setBrush(self.bg_color)
        painter.drawPath(path)
        
        # 绘制文本
        painter.setPen(self.text_color)
        painter.drawText(rect, Qt.AlignCenter | Qt.TextWordWrap, self.current_text)

    def _get_arrow_path(self, rect):
        """获取箭头路径"""
        arrow_path = QPainterPath()
        arrow_x = self.width() // 2
        arrow_size = self.arrow_size
        
        if self.arrow_direction == "top":
            arrow_path.moveTo(arrow_x - arrow_size, rect.top())
            arrow_path.lineTo(arrow_x, rect.top() - arrow_size)
            arrow_path.lineTo(arrow_x + arrow_size, rect.top())
        elif self.arrow_direction == "bottom":
            arrow_path.moveTo(arrow_x - arrow_size, rect.bottom())
            arrow_path.lineTo(arrow_x, rect.bottom() + arrow_size)
            arrow_path.lineTo(arrow_x + arrow_size, rect.bottom())
        
        return arrow_path

    def adjust_size(self, text):
        """根据文本调整气泡大小"""
        fm = self.fontMetrics()
        max_width, min_width, padding = 300, 150, 30
        
        text_rect = fm.boundingRect(0, 0, max_width - padding, 0, Qt.AlignCenter | Qt.TextWordWrap, text)
        ideal_width = max(min_width, min(text_rect.width() + padding, max_width))
        
        # 重新计算高度
        text_rect = fm.boundingRect(0, 0, ideal_width - padding, 0, Qt.AlignCenter | Qt.TextWordWrap, text)
        ideal_height = text_rect.height() + padding
        self.setFixedSize(ideal_width, ideal_height)

    def adjust_position(self):
        """调整位置确保不超出主窗口"""
        if not self.parent_window:
            return
        
        char_geo = self.parent_window.character_label.geometry()
        
        # 计算可用空间
        space_above = char_geo.y()
        space_below = self.parent_window.height() - (char_geo.y() + char_geo.height())
        
        # 根据空间决定气泡位置和箭头方向
        if space_above >= self.height() + 10:
            ideal_y = char_geo.y() - self.height() - 10
            self.set_arrow_direction("bottom")
        elif space_below >= self.height() + 10:
            ideal_y = char_geo.y() + char_geo.height() + 10
            self.set_arrow_direction("top")
        else:
            ideal_y = char_geo.y() - self.height() - 10
            self.set_arrow_direction("bottom")
        
        # 水平居中
        character_center_x = char_geo.x() + char_geo.width() // 2
        bubble_x = max(0, min(character_center_x - self.width() // 2, self.parent_window.width() - self.width()))
        
        self.move(bubble_x, ideal_y)


class TalkManager(QObject):
    """对话管理器，处理所有对话相关的逻辑"""
    
    def __init__(self, api, history_manager, animation_manager, parent_window, memory_manager, heart_manager=None):
        super().__init__()
        self.api = api
        self.history_manager = history_manager
        self.animation_manager = animation_manager
        self.parent_window = parent_window
        self.memory_manager = memory_manager
        self.heart = heart_manager if heart_manager else HeartManager()
        
        # 创建并配置气泡
        self.speech_bubble = SpeechBubble(parent_window)
        self.speech_bubble.set_parent_window(parent_window)
        self.speech_bubble.animation_manager = animation_manager
        
        # 对话状态
        self.is_typing = False
    
    def show_bubble(self, text: str):
        """显示气泡"""
        if not text:
            return
        
        # 设置文本并开始分段显示
        self.speech_bubble.setText(text)
    
    def send_msg(self, user_input: str):
        """处理发送消息"""
        if self.is_typing:
            self.clear_current_display()
        if self.memory_manager:
            self.memory_manager.check_and_consolidate()
        
        # 添加用户消息到历史记录
        self.history_manager.add_talk("user", user_input)

        # 显示思考状态
        if self.animation_manager:
            self.animation_manager.set_thinking_state()
        
        # 获取回复
        thread = Thread(target=self._get_ai_response_thread, args=(user_input,), daemon=True)
        thread.start()
    
    def _invoke_main_thread(self, method_name, *args):
        """在主线程调用方法"""
        if not args:
            QMetaObject.invokeMethod(self.parent_window, method_name, Qt.QueuedConnection)
        else:
            QMetaObject.invokeMethod(self.parent_window, method_name, Qt.QueuedConnection, *[Q_ARG(str, arg) for arg in args])
    
    def clear_current_display(self):
        """清除当前显示"""
        self.speech_bubble.type_timer.stop()
        self.speech_bubble.wait_timer.stop()
        # 重置段落状态
        self.speech_bubble.paragraphs = []
        self.speech_bubble.current_paragraph_index = 0
        self.speech_bubble.hide()
        self.is_typing = False

    def _get_ai_response_thread(self, user_input):
        """获取回复并判断好感度"""
        try:
            response = self.api.get_response(user_input)
            self.history_manager.add_talk("assistant", response)
            
            # 判断好感度变化
            change = self.heart.judge_change(user_input, response)
            if change is not None:
                self.heart.update(change)
                self.heart.log_heart_change_to_last_talk(change)
            
            # 在主线程显示回复
            self._invoke_main_thread("display_ai_response", response)
        except Exception as e:
            self._invoke_main_thread("display_ai_response", f"获取回复时出错: {str(e)}")
        finally:
            self.is_typing = False
            self._invoke_main_thread("on_talk_complete")