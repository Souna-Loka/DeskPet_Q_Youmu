from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, QMenu, QAction
from PyQt5.QtGui import QIcon
from utils.config import Config
import os


class IconManager:
    """管理任务栏图标"""
    
    def __init__(self, parent_window=None):
        """初始化任务栏图标管理器"""
        self.tray_icon = None
        self.parent_window = parent_window
        
    def create_tray_icon(self):
        """创建并显示任务栏图标"""
        if self.tray_icon is not None:
            return
            
        # 获取图标文件路径
        icon_path = os.path.join(Config.IMAGE_PATH, "icon.png")
            
        # 创建QIcon
        icon = QIcon(icon_path)
            
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("桌宠")
        
        # 创建右键菜单
        menu = QMenu()
        
        # 添加退出动作
        exit_action = QAction("退出", menu)
        exit_action.triggered.connect(self._on_exit)
        menu.addAction(exit_action)
        
        # 设置菜单到托盘图标
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
    def remove_tray_icon(self):
        """移除任务栏图标"""
        if self.tray_icon is not None:
            self.tray_icon.hide()
            self.tray_icon = None
    
    def _on_exit(self):
        """处理退出动作"""
        if self.parent_window:
            self.parent_window.close()
        else:
            QApplication.quit()