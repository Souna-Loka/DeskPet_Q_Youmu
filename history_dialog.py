from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QTextCharFormat
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, 
    QPushButton, QScrollArea, QFrame, QSizePolicy,
    QCalendarWidget, QListWidget, QListWidgetItem, QStackedWidget
)
from config import Config
from heart import HeartManager  # 引入好感度管理器

class HistoryDialog(QDialog):
    """历史记录对话框"""
    
    ROLE_STYLES = {
        "event": {
            "role_text": "互动",
            "header_color": "#8e44ad",
            "bg_color": "#f5e8ff",
            "border_color": "#d6a2e4"
        },
        "user": {
            "role_text": "你",
            "header_color": "#3498db",
            "bg_color": "#e3f2fd",
            "border_color": "#bbdefb"
        },
        "assistant": {
            "role_text": "桌宠",
            "header_color": "#2ecc71",
            "bg_color": "#e8f5e9",
            "border_color": "#c8e6c9"
        }
    }

    # 长期记忆统一样式
    MEMORY_STYLE = {
        "header_color": "#666666",
        "bg_color": "#f0f0f0",
        "border_color": "#cccccc"
    }

    def __init__(self, history_manager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.parent_window = parent
        self.filter_date = None
        
        # 初始化好感度管理器
        self.heart = HeartManager()
        
        # 获取桌宠名
        self.pet_name = "桌宠"
        if parent and hasattr(parent, 'user_info_loader'):
            self.pet_name = parent.user_info_loader.info.get("oc_name", "桌宠")
        
        # 获取用户名
        self.user_name = "你"
        if parent and hasattr(parent, 'user_info_loader'):
            self.user_name = parent.user_info_loader.info.get("nickname", "你")
        
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("对话历史记录")
        self.setMinimumSize(670, 450)
        self.resize(720, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 主水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(120)
        self.nav_list.addItem(QListWidgetItem("历史记录"))
        self.nav_list.addItem(QListWidgetItem("长期记忆"))
        
        # 设置导航栏样式
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                border: none;
                color: #ecf0f1;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #34495e;
            }
            QListWidget::item:hover {
                background-color: #34495e;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        main_layout.addWidget(self.nav_list)
        
        # 右侧内容
        self.content_stack = QStackedWidget()
        
        # 创建历史记录页面
        self.history_page = self._create_history_page()
        self.content_stack.addWidget(self.history_page)
        
        # 创建长期记忆页面
        self.memory_page = self._create_memory_page()
        self.content_stack.addWidget(self.memory_page)
        
        main_layout.addWidget(self.content_stack, 1)

    def _create_history_page(self):
        """创建历史记录页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("对话历史记录")
        font = QFont(Config.FONT_FAMILY, 16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("QLabel { color: #333; padding-bottom: 4px; }")
        header_layout.addWidget(title_label)
        
        self.calendar_button = QPushButton("📅")
        self.calendar_button.setFixedSize(32, 32)
        self.calendar_button.setToolTip("按日期筛选")
        self.calendar_button.clicked.connect(self.toggle_calendar)
        header_layout.addWidget(self.calendar_button)
        
        layout.addLayout(header_layout)

        # 日历控件
        self._setup_calendar(layout)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("content_widget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 15, 5)
        self.content_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area, 1)
        
        # 页面样式
        page.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QWidget#content_widget { background-color: transparent; }
        """)
        
        return page

    def _create_memory_page(self):
        """创建长期记忆页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("长期记忆")
        font = QFont(Config.FONT_FAMILY, 16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setStyleSheet("QLabel { color: #333; padding-bottom: 4px; }")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 好感度显示区域
        self.favor_label = QLabel()
        self.favor_label.setFont(QFont(Config.FONT_FAMILY, 11))
        self.favor_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #fdf2f2;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 8px;
            }
        """)
        self._update_favor_display()
        layout.addWidget(self.favor_label)
        
        # 滚动区域
        self.memory_scroll_area = QScrollArea()
        self.memory_scroll_area.setWidgetResizable(True)
        self.memory_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.memory_scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.memory_content_widget = QWidget()
        self.memory_content_widget.setObjectName("memory_content_widget")
        self.memory_content_layout = QVBoxLayout(self.memory_content_widget)
        self.memory_content_layout.setContentsMargins(5, 5, 15, 5)
        self.memory_content_layout.setSpacing(12)
        
        self.memory_scroll_area.setWidget(self.memory_content_widget)
        layout.addWidget(self.memory_scroll_area, 1)
        
        # 页面样式
        page.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QWidget#memory_content_widget { background-color: transparent; }
        """)
        
        return page

    def _update_favor_display(self):
        """更新好感度显示"""
        score = self.heart.score
        level = self.heart.get_level()
        self.favor_label.setText(f"【{self.pet_name}】当前好感度：{score}（{level}）")

    def on_nav_changed(self, index):
        """导航切换事件"""
        self.content_stack.setCurrentIndex(index)
        if index == 0:
            self.load_history()
        else:
            # 切换到长期记忆页面时刷新好感度显示
            self._update_favor_display()
            self.load_memories()

    def _setup_calendar(self, layout):
        """设置日历控件"""
        talks = self.history_manager.get_all_talks()
        self.recorded_dates = {t["timestamp"][:10] for t in talks}
        
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.hide()
        self.calendar.clicked.connect(self.filter_by_date)
        
        if self.recorded_dates:
            dates = sorted(self.recorded_dates)
            self.calendar.setDateRange(QDate.fromString(dates[0], "yyyy-MM-dd"), QDate.fromString(dates[-1], "yyyy-MM-dd"))
        layout.addWidget(self.calendar)

    def load_history(self):
        """加载历史记录"""
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
        
        for talk in reversed(self.history_manager.get_all_talks()):
            if not self.filter_date or talk["timestamp"].startswith(self.filter_date):
                self.content_layout.insertWidget(0, self.create_talk_bubble(talk))

    def load_memories(self):
        """加载长期记忆"""
        # 刷新好感度显示
        self._update_favor_display()
        
        # 清空现有内容
        while self.memory_content_layout.count() > 0:
            item = self.memory_content_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()
        
        # 获取长期记忆数据
        memories = []
        if self.parent_window and hasattr(self.parent_window, 'memory_manager'):
            memories = self.parent_window.memory_manager.long_memories
        
        # 显示记忆气泡
        for memory in reversed(memories):
            self.memory_content_layout.insertWidget(0, self.create_memory_bubble(memory))
        
        # 如果没有记忆，显示提示
        if not memories:
            tip_label = QLabel("暂无长期记忆，与桌宠多聊聊会生成哦~")
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet("QLabel { color: #999; padding: 20px; font-size: 12px; }")
            self.memory_content_layout.addWidget(tip_label)

    def toggle_calendar(self):
        """切换日历显示/隐藏"""
        self.calendar.setVisible(not self.calendar.isVisible())
        if not self.calendar.isVisible():
            return
            
        gray_format = QTextCharFormat()
        gray_format.setForeground(Qt.gray)
        
        current = self.calendar.selectedDate()
        first_day = QDate(current.year(), current.month(), 1)
        last_day = QDate(current.year(), current.month(), first_day.daysInMonth())
        
        current_day = QDate(first_day)
        while current_day <= last_day:
            date_str = current_day.toString("yyyy-MM-dd")
            self.calendar.setDateTextFormat(current_day, gray_format if date_str not in self.recorded_dates else QTextCharFormat())
            current_day = current_day.addDays(1)

    def filter_by_date(self, date):
        """根据选择的日期筛选记录"""
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.recorded_dates:
            self.filter_date = date_str
            self.load_history()

    def create_talk_bubble(self, talk):
        """创建对话气泡"""
        bubble_frame = QFrame()
        bubble_frame.setObjectName("bubble_frame")
        bubble_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        style = self.ROLE_STYLES.get(talk["role"], self.ROLE_STYLES["assistant"])
        bubble_frame.setStyleSheet(f"""
            QFrame#bubble_frame {{
                background-color: {style['bg_color']};
                border: 1px solid {style['border_color']};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        
        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(8)
        
        # 头部
        header_layout = QHBoxLayout()
        if talk["role"] == "user":
            role_display = self.user_name
        elif talk["role"] == "assistant":
            role_display = self.pet_name
        else:
            role_display = style['role_text'] 
        header_label = QLabel(f"{talk['timestamp']} - {role_display}")
        header_font = QFont(Config.FONT_FAMILY, Config.HISTORY_HEADER_FONT_SIZE)
        header_label.setFont(header_font)
        header_label.setStyleSheet(f"QLabel {{ color: {style['header_color']}; font-weight: bold; background-color: transparent;}}")
        header_layout.addWidget(header_label)
        
        # 显示好感度变化
        if 'heartchange' in talk:
            heart_change = talk['heartchange']
            # 根据正负值设置颜色：增加用红色，减少用蓝色
            if heart_change.startswith('+'):
                heart_color = '#e74c3c'
            elif heart_change.startswith('-'):
                heart_color = '#3498db'
            else:
                heart_color = '#95a5a6'
            
            heart_label = QLabel(f"(好感度{heart_change})")
            heart_label.setFont(QFont(Config.FONT_FAMILY, 7))
            heart_label.setStyleSheet(f"QLabel {{ color: {heart_color}; font-weight: bold; background-color: transparent;}}")
            header_layout.addWidget(heart_label)
        
        header_layout.addStretch()
        
        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.setFixedSize(60, 24)
        delete_button.setFont(QFont(Config.FONT_FAMILY, Config.HISTORY_BUTTON_FONT_SIZE))
        delete_button.setStyleSheet("""
            QPushButton { background-color: #ff7043; border: none; border-radius: 4px; color: white; font-weight: bold; padding: 2px 8px; }
            QPushButton:hover { background-color: #ff5722; }
            QPushButton:pressed { background-color: #e64a19; }
        """)
        delete_button.clicked.connect(lambda checked, d_id=talk['id']: self.delete_talk(d_id))
        header_layout.addWidget(delete_button)
        
        bubble_layout.addLayout(header_layout)
        
        # 内容文本
        content_label = QLabel(talk["content"])
        content_label.setObjectName("content_label")
        content_label.setFont(QFont(Config.FONT_FAMILY, Config.HISTORY_FONT_SIZE))
        content_label.setStyleSheet("QLabel { color: #333333; border: none; background-color: transparent; }")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bubble_layout.addWidget(content_label)
        
        return bubble_frame

    def create_memory_bubble(self, memory):
        """创建长期记忆气泡"""
        bubble_frame = QFrame()
        bubble_frame.setObjectName("memory_bubble_frame")
        bubble_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        style = self.MEMORY_STYLE
        bubble_frame.setStyleSheet(f"""
            QFrame#memory_bubble_frame {{
                background-color: {style['bg_color']};
                border: 1px solid {style['border_color']};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        
        bubble_layout = QVBoxLayout(bubble_frame)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(8)
        
        # 头部（只显示时间，不显示角色）
        header_layout = QHBoxLayout()
        header_label = QLabel(f"{memory['timestamp']}")
        header_font = QFont(Config.FONT_FAMILY, Config.HISTORY_HEADER_FONT_SIZE)
        header_label.setFont(header_font)
        header_label.setStyleSheet(f"QLabel {{ color: {style['header_color']}; font-weight: bold; background-color: transparent;}}")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.setFixedSize(60, 24)
        delete_button.setFont(QFont(Config.FONT_FAMILY, Config.HISTORY_BUTTON_FONT_SIZE))
        delete_button.setStyleSheet("""
            QPushButton { background-color: #ff7043; border: none; border-radius: 4px; color: white; font-weight: bold; padding: 2px 8px; }
            QPushButton:hover { background-color: #ff5722; }
            QPushButton:pressed { background-color: #e64a19; }
        """)
        # 使用memory的id删除
        delete_button.clicked.connect(lambda checked, m_id=memory['id']: self.delete_memory(m_id))
        header_layout.addWidget(delete_button)
        
        bubble_layout.addLayout(header_layout)
        
        # 内容文本
        content_label = QLabel(memory["content"])
        content_label.setObjectName("memory_content_label")
        content_label.setFont(QFont(Config.FONT_FAMILY, Config.HISTORY_FONT_SIZE))
        content_label.setStyleSheet("QLabel { color: #333333; border: none; background-color: transparent; }")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bubble_layout.addWidget(content_label)
        
        return bubble_frame

    def _show_silent_confirm(self, title, message):
        """
        显示静默确认对话框
        返回：True(是), False(否)
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(320, 140)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 消息标签
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { font-size: 13px; color: #2c3e50; padding: 5px; }")
        layout.addWidget(label)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 否按钮
        no_button = QPushButton("否")
        no_button.setFixedSize(60, 28)
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        no_button.clicked.connect(dialog.reject)
        button_layout.addWidget(no_button)
        
        # 是按钮
        yes_button = QPushButton("是")
        yes_button.setFixedSize(60, 28)
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #ff7043;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff5722;
            }
        """)
        yes_button.clicked.connect(dialog.accept)
        button_layout.addWidget(yes_button)
        
        layout.addLayout(button_layout)
        
        # 设置对话框样式（淡红色背景表示警告/删除）
        dialog.setStyleSheet("""
            QDialog {
                background-color: #fdf2f2;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
            }
        """)
        
        return dialog.exec_() == QDialog.Accepted

    def _show_silent_info(self, title, message, is_success=True):
        """
        显示静默信息提示框（无系统提示音）
        is_success: True(成功-绿色), False(错误-红色)
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(280, 120)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 消息标签
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { font-size: 13px; color: #2c3e50; padding: 5px; }")
        layout.addWidget(label)
        
        # 确定按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        ok_button.setFixedSize(60, 28)
        ok_button.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 根据类型设置样式
        if is_success:
            bg_color = "#e8f5e9"  # 淡绿色
            border_color = "#81c784"
            btn_color = "#3498db"
            btn_hover = "#2980b9"
        else:
            bg_color = "#ffe6e6"  # 淡红色
            border_color = "#ff9999"
            btn_color = "#e74c3c"
            btn_hover = "#c0392b"
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)
        
        dialog.exec_()

    def delete_talk(self, talk_id):
        """删除对话记录"""
        if self._show_silent_confirm("确认删除", "确定要删除这条记录吗？\n删除后角色将不再记得这条内容。"):
            self.history_manager.delete_talk(talk_id)
            
            if self.parent_window and hasattr(self.parent_window, 'api'):
                self.parent_window.api.update_conversation_history()
            
            self.load_history()
            self._show_silent_info("删除成功", "记录已删除。", is_success=True)

    def delete_memory(self, memory_id):
        """删除长期记忆"""
        if self._show_silent_confirm("确认删除", "确定要删除这条长期记忆吗？\n这是AI总结的重要记忆，删除后可能影响对话连贯性。"):
            if self.parent_window and hasattr(self.parent_window, 'memory_manager'):
                # 从内存中删除
                self.parent_window.memory_manager.long_memories = [
                    m for m in self.parent_window.memory_manager.long_memories 
                    if m['id'] != memory_id
                ]
                # 重新排序id
                for index, memory in enumerate(self.parent_window.memory_manager.long_memories):
                    memory['id'] = index
                # 保存到文件
                self.parent_window.memory_manager.save_long_memory()
                
                self.load_memories()
                # 使用静默提示框替代 QMessageBox.information
                self._show_silent_info("删除成功", "长期记忆已删除。", is_success=True)

    def resizeEvent(self, event):
        """窗口大小改变时重新调整气泡大小"""
        super().resizeEvent(event)
        QTimer.singleShot(50, self._adjust_all_bubbles)

    def _adjust_all_bubbles(self):
        """调整所有气泡的大小"""
        # 调整历史记录气泡
        if hasattr(self, 'scroll_area') and self.scroll_area.isVisible():
            viewport_width = self.scroll_area.viewport().width()
            text_available_width = max(viewport_width - 64, 336)
            
            for i in range(self.content_layout.count() - 1):
                item = self.content_layout.itemAt(i)
                if not (item and item.widget()):
                    continue
                    
                bubble = item.widget()
                content_label = bubble.findChild(QLabel, "content_label")
                if not content_label:
                    continue
                
                # 重新计算高度
                font_metrics = content_label.fontMetrics()
                text_rect = font_metrics.boundingRect(0, 0, text_available_width, 0, Qt.TextWordWrap | Qt.AlignLeft, content_label.text())
                content_label.setMinimumHeight(text_rect.height() + 20)
        
        # 调整长期记忆气泡
        if hasattr(self, 'memory_scroll_area') and self.memory_scroll_area.isVisible():
            viewport_width = self.memory_scroll_area.viewport().width()
            text_available_width = max(viewport_width - 64, 336)
            
            for i in range(self.memory_content_layout.count() - 1):
                item = self.memory_content_layout.itemAt(i)
                if not (item and item.widget()):
                    continue
                    
                bubble = item.widget()
                content_label = bubble.findChild(QLabel, "memory_content_label")
                if not content_label:
                    continue
                
                # 重新计算高度
                font_metrics = content_label.fontMetrics()
                text_rect = font_metrics.boundingRect(0, 0, text_available_width, 0, Qt.TextWordWrap | Qt.AlignLeft, content_label.text())
                content_label.setMinimumHeight(text_rect.height() + 20)