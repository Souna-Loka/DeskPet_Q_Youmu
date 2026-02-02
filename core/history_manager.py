import json
from datetime import datetime
from threading import Lock
from utils.config import Config

class TalkHistoryManager:
    """管理对话历史记录"""
    
    def __init__(self, history_file=None):
        if history_file is None:
            history_file = Config.HISTORY_FILE
        
        self.history_file = history_file
        self.history = []
        self.history_lock = Lock()
        self.load_history()
        self.reorganize_ids()
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                self.history = json.loads(content) if content else []
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.history = []
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            abs_path = Config.get_full_path(self.history_file)
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def _get_min_available_id(self):
        """获取最小的可用ID"""
        if not self.history:
            return 0
        used_ids = sorted([talk["id"] for talk in self.history])
        for i, used_id in enumerate(used_ids):
            if used_id != i:
                return i
        return len(used_ids)
    
    def reorganize_ids(self):
        """重新整理所有记录的ID，使其从0开始连续"""
        with self.history_lock:
            needs_reorganize = False
            for index, talk in enumerate(self.history):
                if talk["id"] != index:
                    needs_reorganize = True
                    break
            
            if needs_reorganize:
                print("检测到ID不连续，正在重新整理...")
                # 重新分配ID
                for index, talk in enumerate(self.history):
                    talk["id"] = index
                self.save_history()
                print("ID整理完成")
    
    def add_talk(self, role, content):
        """添加对话记录"""
        with self.history_lock:
            talk_entry = {
                "id": self._get_min_available_id(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "role": role,
                "content": content
            }
            self.history.append(talk_entry)
            self.save_history()
    
    def get_all_talks(self):
        """获取所有对话记录"""
        with self.history_lock:
            return self.history.copy()
    
    def delete_talk(self, talk_id):
        """删除对话记录"""
        with self.history_lock:
            self.history = [d for d in self.history if d["id"] != talk_id]
            for index, talk in enumerate(self.history):
                talk["id"] = index
            self.save_history()