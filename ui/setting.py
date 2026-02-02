from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QWidget, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt
from utils.config import Config
from utils.begin import DEFAULT_FAVORABILITY
from utils.autostart import set_autostart, is_autostart_enabled
import json
import os


class SettingsDialog(QDialog):
    """设置对话框"""
    
    # 统一样式常量
    STYLE = {
        "title": "font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;",
        "input": """
            QLineEdit, QTextEdit, QSpinBox {
                padding: 8px; border: 1px solid #ddd; border-radius: 4px; background-color: white;
            }
            QSpinBox { min-width: 60px; padding: 5px; }
        """,
        "table": """
            QTableWidget { background-color: white; border: 1px solid #ddd; border-radius: 4px; gridline-color: #e0e0e0; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background-color: #f0f0f0; padding: 8px; border: 1px solid #ddd; font-weight: bold; }
        """,
        "nav": """
            QListWidget { background-color: #2c3e50; border: none; color: #ecf0f1; font-size: 14px; }
            QListWidget::item { padding: 12px 15px; border-bottom: 1px solid #34495e; }
            QListWidget::item:hover { background-color: #34495e; }
            QListWidget::item:selected { background-color: #3498db; color: white; }
        """,
        "btn_primary": "background-color: #3498db; color: white; border: none; border-radius: 4px; font-size: 12px; padding: 5px 15px;",
        "btn_secondary": "background-color: #95a5a6; color: white; border: none; border-radius: 4px; font-size: 12px; padding: 5px 15px;",
        "dialog_success": "background-color: #e8f5e9; border: 1px solid #81c784; border-radius: 8px;",
        "dialog_error": "background-color: #ffe6e6; border: 1px solid #ff9999; border-radius: 8px;"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.init_ui()

    def init_ui(self):
        """初始化设置界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(100)
        for text in ["用户信息", "角色设定", "系统", "API配置"]:
            self.nav_list.addItem(QListWidgetItem(text))
        self.nav_list.setStyleSheet(self.STYLE["nav"])
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        main_layout.addWidget(self.nav_list)

        # 右侧内容区
        self.content_area = QStackedWidget()
        self.pages = {
            "user": self._create_user_page(),
            "char": self._create_character_page(),
            "sys": self._create_system_page(),
            "api": self._create_api_page()
        }
        for page in self.pages.values():
            self.content_area.addWidget(page)
        
        main_layout.addWidget(self.content_area, 1)
        self.setStyleSheet(f"QDialog {{ background-color: #f5f5f5; border-radius: 8px; }}")

    def _on_nav_changed(self, index):
        """导航切换"""
        self.content_area.setCurrentIndex(index)
        page_key = list(self.pages.keys())[index]
        if hasattr(self, f"_refresh_{page_key}_page"):
            getattr(self, f"_refresh_{page_key}_page")()

    def _create_title(self, text):
        """创建统一标题标签"""
        label = QLabel(text)
        label.setStyleSheet(self.STYLE["title"])
        return label

    def _create_input_field(self, layout, label_text, default_value="", is_textarea=False, height=80):
        """创建输入字段"""
        layout.addWidget(QLabel(f"<b>{label_text}</b>"))
        if is_textarea:
            field = QTextEdit()
            field.setPlainText(default_value)
            field.setFixedHeight(height)
        else:
            field = QLineEdit(default_value)
        field.setStyleSheet(self.STYLE["input"])
        layout.addWidget(field)
        return field

    def _create_page_layout(self):
        """创建统一页面布局"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        return page, layout

    def _add_action_buttons(self, layout, save_slot, reset_slot):
        """添加保存/重置按钮组"""
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        for text, slot, is_primary in [("保存", save_slot, True), ("重置", reset_slot, False)]:
            btn = QPushButton(text)
            btn.setFixedSize(60, 28)
            btn.setStyleSheet(self.STYLE["btn_primary"] if is_primary else self.STYLE["btn_secondary"])
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _create_user_page(self):
        """用户信息页"""
        page, layout = self._create_page_layout()
        layout.addWidget(self._create_title("用户信息"))

        self.user_inputs = {}
        defaults = {"nickname": "用户", "birthday": "2000-01-01", "oc_name": "桌宠", "relationship": "朋友"}
        data = self._load_config(Config.USER_INFO_FILE, defaults)
        self.user_data_original = data.copy()

        for label, key in [("用户名", "nickname"), ("你的生日", "birthday"), 
                          ("桌宠名", "oc_name"), ("关系", "relationship")]:
            field = self._create_input_field(layout, label, data.get(key, defaults[key]))
            self.user_inputs[key] = field

        self._add_action_buttons(layout, self.save_user_info, self.reset_user_info)
        return page

    def _create_character_page(self):
        """角色设定页"""
        page, layout = self._create_page_layout()
        layout.addWidget(self._create_title("角色设定"))

        defaults = {"content": "你是一个可爱的桌宠，性格活泼开朗，喜欢和主人互动。", 
                   "favorability": DEFAULT_FAVORABILITY}
        data = self._load_config(Config.CHARACTER_FILE, defaults)
        
        self.char_original = data.get('content', defaults['content'])
        self.favor_original = data.get('favorability', defaults['favorability'])

        # 角色设定内容
        self.char_input = self._create_input_field(layout, "角色设定内容", self.char_original, 
                                                   is_textarea=True, height=100)

        # 好感度表格
        layout.addWidget(QLabel("<b>好感度等级配置</b>"))
        self.favor_table = QTableWidget()
        self.favor_table.setColumnCount(4)
        self.favor_table.setHorizontalHeaderLabels(["名称", "分数下限", "分数上限", "行为描述"])
        self.favor_table.setStyleSheet(self.STYLE["table"])
        self._load_favorability(self.favor_original)
        
        self.favor_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.favor_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.favor_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.favor_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.favor_table.setFixedHeight(200)
        layout.addWidget(self.favor_table)

        self._add_action_buttons(layout, self.save_character_info, self.reset_character_info)
        return page

    def _create_system_page(self):
        """系统设置页"""
        page, layout = self._create_page_layout()
        layout.addWidget(self._create_title("系统设置"))

        defaults = {"scale": 100, "always_on_top": True, "show_tray_icon": True}
        self.sys_data = self._load_config(Config.SETTING_FILE, defaults)
        self.sys_original = self.sys_data.copy()

        # 缩放
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("<b>桌宠大小</b>"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(25, 200)
        self.scale_spin.setValue(self.sys_data["scale"])
        self.scale_spin.setSuffix("%")
        self.scale_spin.setStyleSheet(self.STYLE["input"])
        scale_layout.addWidget(self.scale_spin)
        scale_layout.addStretch()
        layout.addLayout(scale_layout)

        # 复选框
        self.topmost_cb = QCheckBox("窗口置顶")
        self.topmost_cb.setChecked(self.sys_data["always_on_top"])
        self.topmost_cb.setStyleSheet("QCheckBox { spacing: 8px; margin-top: 10px; }")
        layout.addWidget(self.topmost_cb)

        self.tray_cb = QCheckBox("显示任务栏图标")
        self.tray_cb.setChecked(self.sys_data["show_tray_icon"])
        self.tray_cb.setStyleSheet("QCheckBox { spacing: 8px; margin-top: 5px; }")
        layout.addWidget(self.tray_cb)

        self.autostart_cb = QCheckBox("开机自启动")
        self.autostart_cb.setChecked(is_autostart_enabled())
        self.autostart_cb.setStyleSheet("QCheckBox { spacing: 8px; margin-top: 5px; }")
        layout.addWidget(self.autostart_cb)

        self._add_action_buttons(layout, self.save_system_settings, self.reset_system_settings)
        return page

    def _create_api_page(self):
        """API配置页"""
        page, layout = self._create_page_layout()
        layout.addWidget(self._create_title("API配置"))

        defaults = {
            "chat_api": {"api_key": "", "api_url": "https://api.deepseek.com/v1/chat/completions",
                        "model": "deepseek-chat", "temperature": 0.8, "max_tokens": 900, "stream": False},
            "vision_api": {"api_key": "", "api_url": "https://api.siliconflow.cn/v1/chat/completions",
                          "model": "Pro/THUDM/GLM-4.1V-9B-Thinking", "temperature": 0.8, "max_tokens": 800}
        }
        self.api_data = self._load_config(os.path.join("txt", "api.json"), defaults)
        self.api_original = json.dumps(self.api_data, ensure_ascii=False)

        # 对话API
        layout.addWidget(QLabel("<b>对话API配置</b>"))
        self.chat_inputs = self._create_api_group(layout, self.api_data["chat_api"], 
                                                  ["api_key", "api_url", "model", "temperature", "max_tokens", "stream"])

        layout.addSpacing(15)
        layout.addWidget(QLabel("<b>识图API配置</b>"))
        self.vision_inputs = self._create_api_group(layout, self.api_data["vision_api"],
                                                    ["api_key", "api_url", "model", "temperature", "max_tokens"])

        self._add_action_buttons(layout, self.save_api_settings, self.reset_api_settings)
        return page

    def _create_api_group(self, layout, data, fields):
        """创建API配置输入组"""
        inputs = {}
        for field in fields:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(f"{field.replace('_', ' ').title()}:"))
            
            if field == "stream":
                cb = QCheckBox()
                cb.setChecked(data.get(field, False))
                hbox.addWidget(cb)
                inputs[field] = cb
            elif field in ["temperature"]:
                spin = QSpinBox()
                spin.setRange(0, 100)
                spin.setValue(int(data.get(field, 0.8) * 100))
                spin.setSuffix("%")
                spin.setStyleSheet(self.STYLE["input"])
                hbox.addWidget(spin)
                inputs[field] = spin
            elif field in ["max_tokens"]:
                spin = QSpinBox()
                spin.setRange(100, 4000)
                spin.setValue(data.get(field, 900))
                spin.setStyleSheet(self.STYLE["input"])
                hbox.addWidget(spin)
                inputs[field] = spin
            else:
                edit = QLineEdit(data.get(field, ""))
                if "key" in field:
                    edit.setPlaceholderText("请输入API密钥")
                edit.setStyleSheet(self.STYLE["input"])
                hbox.addWidget(edit)
                inputs[field] = edit
            
            hbox.addStretch()
            layout.addLayout(hbox)
        return inputs

    def _load_config(self, path, default):
        """加载配置"""
        full_path = Config.get_full_path(path) if not os.path.isabs(path) else path
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(default, dict) and isinstance(loaded, dict):
                        default_copy = default.copy()
                        default_copy.update(loaded)
                        return default_copy
                    return loaded
            except Exception as e:
                print(f"加载配置失败 {path}: {e}")
        return default

    def _save_config(self, path, data):
        """保存配置"""
        full_path = Config.get_full_path(path) if not os.path.isabs(path) else path
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_favorability(self, data):
        """加载好感度到表格"""
        self.favor_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.favor_table.setItem(row, 0, QTableWidgetItem(item.get('label', '')))
            range_val = item.get('range', [0, 0])
            self.favor_table.setItem(row, 1, QTableWidgetItem(str(range_val[0])))
            self.favor_table.setItem(row, 2, QTableWidgetItem(str(range_val[1])))
            self.favor_table.setItem(row, 3, QTableWidgetItem(item.get('desc', '')))

    def _get_favorability(self):
        """从表格获取好感度配置"""
        result = []
        for row in range(self.favor_table.rowCount()):
            try:
                label = self.favor_table.item(row, 0).text().strip()
                rmin = int(self.favor_table.item(row, 1).text())
                rmax = int(self.favor_table.item(row, 2).text())
                desc = self.favor_table.item(row, 3).text().strip()
                if label and desc:
                    result.append({"id": row, "label": label, "range": [rmin, rmax], "desc": desc})
            except (ValueError, AttributeError):
                continue
        return result

    def _show_message(self, msg, is_error=False):
        """统一消息提示"""
        dlg = QDialog(self)
        dlg.setWindowTitle("提示")
        dlg.setFixedSize(280, 120)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel(msg)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        btn = QPushButton("确定")
        btn.setFixedSize(60, 28)
        btn.setStyleSheet(self.STYLE["btn_primary"])
        btn.clicked.connect(dlg.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        
        dlg.setStyleSheet(self.STYLE["dialog_error"] if is_error else self.STYLE["dialog_success"])
        dlg.exec_()

    def _reload_parent(self):
        """通知父窗口重载配置"""
        if self.parent_window:
            if hasattr(self.parent_window, 'reload_config'):
                self.parent_window.reload_config()
            if hasattr(self.parent_window, 'reload_api_config'):
                self.parent_window.reload_api_config()

    # --- 保存/重置方法 ---

    def save_user_info(self):
        """保存用户信息"""
        data = {k: v.text().strip() for k, v in self.user_inputs.items()}
        try:
            self._save_config(Config.USER_INFO_FILE, data)
            self.user_data_original = data
            self._reload_parent()
            self._show_message("修改成功了哦~")
        except Exception as e:
            self._show_message(f"保存失败惹...: {e}", True)

    def reset_user_info(self):
        """重置用户信息"""
        for k, v in self.user_inputs.items():
            v.setText(self.user_data_original.get(k, ''))
        self._show_message("信息已经重置惹~")

    def save_character_info(self):
        """保存角色设定"""
        content = self.char_input.toPlainText().strip()
        favor = self._get_favorability()
        try:
            data = {"content": content, "favorability": favor}
            existing = self._load_config(Config.CHARACTER_FILE, {})
            existing.update(data)
            self._save_config(Config.CHARACTER_FILE, existing)
            self.char_original = content
            self.favor_original = favor
            self._reload_parent()
            self._show_message("保存成功了哦~")
        except Exception as e:
            self._show_message(f"保存失败惹...: {e}", True)

    def reset_character_info(self):
        """重置角色设定"""
        self.char_input.setPlainText(self.char_original)
        self._load_favorability(self.favor_original)
        self._show_message("角色设定已经重置惹~")

    def save_system_settings(self):
        """保存系统设置"""
        settings = {
            "scale": self.scale_spin.value(),
            "always_on_top": self.topmost_cb.isChecked(),
            "show_tray_icon": self.tray_cb.isChecked()
        }
        try:
            self._save_config(Config.SETTING_FILE, settings)
            self.sys_original = settings.copy()
            if self.parent_window and hasattr(self.parent_window, 'apply_system_settings'):
                self.parent_window.apply_system_settings(settings)
            set_autostart(self.autostart_cb.isChecked())
            self._show_message("系统设置保存成功~")
        except Exception as e:
            self._show_message(f"保存失败: {e}", True)

    def reset_system_settings(self):
        """重置系统设置"""
        self.scale_spin.setValue(self.sys_original.get("scale", 100))
        self.topmost_cb.setChecked(self.sys_original.get("always_on_top", True))
        self.tray_cb.setChecked(self.sys_original.get("show_tray_icon", True))
        self.autostart_cb.setChecked(is_autostart_enabled())
        self._show_message("设置已重置~")

    def save_api_settings(self):
        """保存API配置"""
        def extract(inputs, is_chat=True):
            data = {}
            for k, v in inputs.items():
                if isinstance(v, QCheckBox):
                    data[k] = v.isChecked()
                elif isinstance(v, QSpinBox):
                    val = v.value()
                    data[k] = val / 100.0 if k == "temperature" else val
                else:
                    data[k] = v.text().strip()
            return data
        
        api_data = {"chat_api": extract(self.chat_inputs), "vision_api": extract(self.vision_inputs, False)}
        
        try:
            self._save_config(os.path.join("txt", "api.json"), api_data)
            self.api_original = json.dumps(api_data, ensure_ascii=False)
            self._reload_parent()
            self._show_message("API配置保存成功~")
        except Exception as e:
            self._show_message(f"保存失败: {e}", True)

    def reset_api_settings(self):
        """重置API配置"""
        try:
            orig = json.loads(self.api_original)
            for section, inputs in [("chat_api", self.chat_inputs), ("vision_api", self.vision_inputs)]:
                data = orig.get(section, {})
                for k, v in inputs.items():
                    val = data.get(k)
                    if isinstance(v, QCheckBox):
                        v.setChecked(val if isinstance(val, bool) else False)
                    elif isinstance(v, QSpinBox):
                        v.setValue(int(val * 100) if k == "temperature" and val else val or 0)
                    else:
                        v.setText(str(val) if val else "")
            self._show_message("API配置已重置~")
        except Exception as e:
            self._show_message(f"重置失败: {e}", True)