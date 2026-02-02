import re, os, json
from datetime import datetime
from PyQt5.QtCore import Qt, QPoint, QTimer, QRectF, pyqtSlot
from PyQt5.QtGui import QPainterPath, QRegion, QMouseEvent
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QMenu, QAction
from utils.config import Config
from utils.loader import CharacterLoader, UserInfoLoader
from core.history_manager import TalkHistoryManager
from api.api_client import DeepSeekAPI, VisionAPI
from ui.animation_manager import AnimationManager
from ui.talk import TalkManager
from ui.history_dialog import HistoryDialog
from core.memory_manager import MemoryManager
from ui.setting import SettingsDialog
from ui.icon import IconManager
from core.time1 import TimeAnnouncer
from core.heart import HeartManager
from utils.look import capture_screen_base64


class DeskPetWindow(QWidget):
    """桌宠主窗口"""

    # 样式常量
    STYLES = {
        "input_field": """
            QLineEdit {
                background-color: rgba(255, 255, 255, 240);
                border: 2px solid rgba(100, 150, 255, 200);
                padding: 3px;
                font-size: 8px;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                border-radius: 10px
            }
            QLineEdit:focus {
                border-color: rgba(50, 120, 255, 255);
                background-color: rgba(255, 255, 255, 255);
            }
        """,
        "send_button": """
            QPushButton {
                background-color: rgba(100, 150, 255, 220);
                border: none;
                color: white;
                font-weight: bold;
                font-size: 8px;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                border-radius: 10px
            }
            QPushButton:hover { background-color: rgba(80, 130, 235, 240); }
            QPushButton:pressed { background-color: rgba(60, 110, 215, 255); }
            QPushButton:disabled { background-color: rgba(150, 150, 150, 150); }
        """,
        "context_menu": """
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                min-width: 80px;
                font-size: 10px;
                font-family: 'Microsoft YaHei', 'Segoe UI';
            }
            QMenu::item {
                padding: 6px 15px;
                border-radius: 3px;
            }
            QMenu::item:selected { background-color: rgba(100, 150, 255, 100); }
            QMenu::separator {
                height: 1px;
                background: rgba(200, 200, 200, 150);
                margin: 3px 0px;
            }
        """
    }

    def __init__(self):
        super().__init__()
        
        # 核心管理器初始化
        self.history_manager = TalkHistoryManager()
        self.user_info_loader = UserInfoLoader()
        self.heart_manager = HeartManager()
        self.memory_manager = MemoryManager(self.history_manager)
        
        # 对话框引用
        self.history_dialog = None
        self.settings_dialog = None
        
        # 角色和提示词
        self.character_prompt = CharacterLoader.load_character()
        
        # API 和对话管理器
        self.api = None
        self.vision_api = None
        self.talk_manager = None
        
        # 输入隐藏定时器
        self.input_timer = QTimer()
        self.input_timer.timeout.connect(self.hide_input_and_button)
        self.input_timer.setSingleShot(True)
        
        # 初始化 UI
        self.init_ui()
        self.setup_window()
        
        # 初始化 API
        self._init_apis()
        
        # 托盘图标
        self.tray_manager = IconManager(self)
        self.tray_manager.create_tray_icon()
        
        # 加载系统设置
        self.load_and_apply_system_settings()
        
        # 整点报时
        self.time_announcer = TimeAnnouncer(self.talk_manager, self.api, self.heart_manager)
        QTimer.singleShot(500, self.show_greeting)
    
    def _init_apis(self):
        """统一初始化 API 和对话管理器"""
        # 公共参数
        common_params = {
            'character_prompt': self.character_prompt,
            'history_manager': self.history_manager,
            'memory_manager': self.memory_manager,
            'heart_manager': self.heart_manager
        }
        
        self.api = DeepSeekAPI(**common_params)
        self.vision_api = VisionAPI(user_info_loader=self.user_info_loader, **common_params)
        
        self.talk_manager = TalkManager(
            self.api, self.history_manager, self.animation_manager, 
            self, self.memory_manager, self.heart_manager
        )

    def init_ui(self):
        """初始化用户界面"""
        self.character_label = QLabel(self)
        self.animation_manager = AnimationManager(self.character_label, heart_manager=self.heart_manager)
        
        # 计算窗口尺寸
        self._recalculate_layout()
        
        # 设置鼠标跟踪
        self.character_label.setMouseTracking(True)
        self.setMouseTracking(True)
        self.dragging = False
        self.drag_position = QPoint()
    
    def _recalculate_layout(self, window_width=None, window_height=None):
        """重新计算并应用窗口布局"""
        char_width = self.character_label.width()
        char_height = self.character_label.height()
        dialog_space = 120
        
        width = window_width or max(char_width + 80, Config.WINDOW_WIDTH)
        height = window_height or (char_height + Config.INPUT_HEIGHT + dialog_space)
        
        self.setFixedSize(width, height)
        
        # 计算输入区域布局
        input_width = width - 150
        input_box_width = input_width - 40
        button_width = 30
        total_input_width = input_box_width + button_width
        start_x = (width - total_input_width) // 2
        
        # 初始化或更新输入框
        if hasattr(self, 'input_field'):
            self.input_field.setFixedSize(input_box_width, Config.INPUT_HEIGHT)
            self.input_field.move(start_x, height - Config.INPUT_HEIGHT - 15)
            self.send_button.setFixedSize(button_width, Config.INPUT_HEIGHT)
            self.send_button.move(start_x + input_box_width + 8, height - Config.INPUT_HEIGHT - 15)
        else:
            self.input_field = QLineEdit(self)
            self.input_field.setPlaceholderText("在这里输入消息...")
            self.input_field.setFixedSize(input_box_width, Config.INPUT_HEIGHT)
            self.input_field.setStyleSheet(self.STYLES["input_field"])
            self.input_field.returnPressed.connect(self.send_msg)
            self.input_field.move(start_x, height - Config.INPUT_HEIGHT - 15)
            self.input_field.hide()
            
            self.send_button = QPushButton("发送", self)
            self.send_button.setFixedSize(button_width, Config.INPUT_HEIGHT)
            self.send_button.setStyleSheet(self.STYLES["send_button"])
            self.send_button.clicked.connect(self.send_msg)
            self.send_button.move(start_x + input_box_width + 8, height - Config.INPUT_HEIGHT - 15)
            self.send_button.hide()
        
        # 角色位置
        char_x = int(start_x + total_input_width // 2 - char_width // 2)
        char_y = height - char_height - Config.INPUT_HEIGHT - 15
        self.character_label.move(char_x, char_y)
        
        return width, height

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if not event:
            return
        
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return
        
        # 检测是否在桌宠区域
        pet_area = self.character_label.geometry().united(self.input_field.geometry()).united(self.send_button.geometry())
        if pet_area.contains(event.pos()):
            if self.input_field.isHidden():
                self.show_input_and_button()
            self.input_timer.stop()
        else:
            if not self.input_timer.isActive() and not self.input_field.isHidden():
                self.input_timer.start(Config.HIDE_INPUT_DELAY)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if not event:
            return
        
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if not event:
            return
        
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """鼠标双击事件"""
        if not event:
            return
        
        if event.button() == Qt.LeftButton and self.character_label.geometry().contains(event.pos()):
            self._handle_poke_event()
            event.accept()
    
    def _handle_poke_event(self):
        """处理戳一戳事件"""
        if self.animation_manager:
            self.animation_manager.close_eyes()
        
        user_name = self.user_info_loader.info.get("nickname", "用户")
        pet_name = self.user_info_loader.info.get("oc_name", "桌宠")
        history = self.history_manager.history
        
        # 合并连续戳
        if history and history[-1]["role"] == "event" and "戳了戳" in history[-1]["content"]:
            last = history[-1]
            content = last["content"]
            last["content"] = re.sub(r"(\d+)次", lambda m: f"{int(m.group(1)) + 1}次", content) if "次" in content else content + "2次"
            last["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.history_manager.save_history()
        else:
            self.history_manager.add_talk("event", f"{user_name}戳了戳{pet_name}")
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if not self.input_timer.isActive() and not self.input_field.isHidden():
            self.input_timer.start(Config.HIDE_INPUT_DELAY)
        event.accept()

    def setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            DeskPetWindow {
                background-color: rgba(240, 248, 255, 230);
                border: 2px solid rgba(100, 150, 255, 180);
            }
        """)
        
        self.setWindowTitle("妖梦")
        screen = self.screen()
        if screen:
            geom = screen.availableGeometry()
            self.move(geom.width() - Config.WINDOW_WIDTH - 20, geom.height() - Config.WINDOW_HEIGHT - 20)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, float(self.width()), float(self.height())), 20, 20)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(self.STYLES["context_menu"])
        
        actions = [
            ("历史记录", self.show_history_dialog),
            None,
            ("设置", self.show_settings_dialog),
            None,
            ("看看屏幕", self.analyze_screen),
            None,
            ("退出", self.close)
        ]
        
        for item in actions:
            if item is None:
                menu.addSeparator()
            else:
                action = QAction(item[0], self)
                action.triggered.connect(item[1])
                menu.addAction(action)
        
        menu.exec_(event.globalPos())

    def show_input_and_button(self):
        """显示输入框和按钮"""
        self.input_field.show()
        self.send_button.show()
        self.raise_()
        self.activateWindow()

    def hide_input_and_button(self):
        """隐藏输入框和按钮"""
        if not self.input_field.hasFocus():
            self.input_field.hide()
            self.send_button.hide()

    def send_msg(self):
        """发送消息"""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        self.send_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.input_field.clear()
        self.talk_manager.send_msg(user_input)

    def show_greeting(self):
        """显示初始问候"""
        hour = datetime.now().hour
        name = self.user_info_loader.info.get("nickname", "用户")
        
        if 5 <= hour < 12:
            greeting = f"早安，{name}"
        elif 12 <= hour < 18:
            greeting = f"午安，{name}"
        else:
            greeting = f"晚安，{name}"
        
        self.talk_manager.show_bubble(greeting)

    @pyqtSlot(str)
    def display_ai_response(self, response):
        """显示AI回复"""
        self.talk_manager.show_bubble(response)

    @pyqtSlot()
    def on_talk_complete(self):
        """对话完成回调"""
        self.send_button.setEnabled(True)
        self.input_field.setEnabled(True)

    def show_history_dialog(self):
        """显示历史记录对话框"""
        if self.history_dialog is not None:
            self.history_dialog.show()
            self.history_dialog.raise_()
            self.history_dialog.activateWindow()
            return
        
        self.history_dialog = HistoryDialog(self.history_manager, self)
        self.history_dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        self.history_dialog.destroyed.connect(self._clear_history_ref)
        self.history_dialog.show()
    
    def _clear_history_ref(self):
        """清理历史对话框引用"""
        self.history_dialog = None

    def show_settings_dialog(self):
        """显示设置对话框"""
        if self.settings_dialog is not None:
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return
        
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        self.settings_dialog.destroyed.connect(self._clear_settings_ref)
        self.settings_dialog.show()
    
    def _clear_settings_ref(self):
        """清理设置对话框引用"""
        self.settings_dialog = None

    def analyze_screen(self):
        """分析屏幕并显示评价"""
        try:
            image_base64 = capture_screen_base64()
            self.animation_manager.set_thinking_state()
            
            from threading import Thread
            Thread(target=self._screen_analysis_thread, args=(image_base64,), daemon=True).start()
        except Exception as e:
            error_msg = f"截图失败: {str(e)}"
            print(error_msg)
            self.talk_manager.show_bubble(error_msg)

    def _screen_analysis_thread(self, image_base64):
        """后台分析屏幕"""
        analysis = self.vision_api.analyze_screen(image_base64)
        self.history_manager.add_talk("assistant", analysis)
        self.api.update_conversation_history()
        
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self, "display_ai_response", 
            Qt.QueuedConnection, 
            Q_ARG(str, analysis)
        )

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 统一清理定时器
        timers_to_stop = [
            ('input_timer', 'input_timer'),
            ('time_announcer', 'timer'),
            ('animation_manager', 'animation_timer'),
            ('animation_manager', 'close_eye_timer'),
        ]
        
        for obj_name, timer_name in timers_to_stop:
            obj = getattr(self, obj_name, None)
            if obj:
                timer = getattr(obj, timer_name, None)
                if timer:
                    timer.stop()
        
        # 清理气泡定时器
        if self.talk_manager and self.talk_manager.speech_bubble:
            bubble = self.talk_manager.speech_bubble
            for timer_name in ['type_timer', 'wait_timer', 'follow_timer']:
                timer = getattr(bubble, timer_name, None)
                if timer:
                    timer.stop()
                    timer.deleteLater()
            bubble.hide()
            bubble.deleteLater()
        
        # 清理对话状态
        if self.talk_manager:
            self.talk_manager.is_typing = False

        # 清理对话框
        for dlg_name in ['history_dialog', 'settings_dialog']:
            dlg = getattr(self, dlg_name, None)
            if dlg:
                dlg.close()
                dlg.deleteLater()
                setattr(self, dlg_name, None)

        # 清理托盘
        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.remove_tray_icon()
        
        event.accept()
        
        # 强制退出
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.quit()

    def reload_config(self):
        """重新加载配置"""
        try:
            self.character_prompt = CharacterLoader.load_character()
            self.user_info_loader = UserInfoLoader()
            self._init_apis()
        except Exception as e:
            print(f"重新加载配置失败: {e}")

    def reload_api_config(self):
        """重新加载API配置"""
        try:
            # 只更新密钥等配置，保持历史记录和记忆
            self._init_apis()
            print("API配置已重新加载")
        except Exception as e:
            print(f"重新加载API配置失败: {e}")

    def load_and_apply_system_settings(self):
        """加载并应用系统设置"""
        defaults = {"scale": 100, "always_on_top": True, "show_tray_icon": True}
        path = Config.get_full_path(Config.SETTING_FILE)
        
        try:
            settings = json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else defaults
        except Exception as e:
            print(f"加载系统设置失败: {e}")
            settings = defaults
        
        self.apply_system_settings(settings)

    def apply_system_settings(self, settings):
        """应用系统设置到窗口"""
        # 置顶设置
        always_on_top = settings.get("always_on_top", True)
        current_flags = self.windowFlags()
        
        has_top_hint = bool(current_flags & Qt.WindowStaysOnTopHint)
        if always_on_top != has_top_hint:
            if always_on_top:
                self.setWindowFlags(current_flags | Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(current_flags & ~Qt.WindowStaysOnTopHint)
            self.show()
        
        # 缩放设置
        scale = settings.get("scale", 100)
        if scale != int(Config.SCALE_FACTOR / 0.15 * 100):
            Config.SCALE_FACTOR = scale / 100.0 * 0.15
            self.animation_manager._load_all_images()
            
            if not self.animation_manager.normal1.isNull():
                new_size = self.animation_manager.normal1.size()
                self.character_label.setFixedSize(new_size)
                self.animation_manager._update_display(self.animation_manager.current_state)
            
            # 重新布局
            self._recalculate_layout()
        
        # 托盘图标
        if self.tray_manager and self.tray_manager.tray_icon:
            self.tray_manager.tray_icon.setVisible(settings.get("show_tray_icon", True))
        
        self.system_settings = settings