import os
import json
from config import Config

class BaseLoader:
    """通用文件加载基类"""
    
    @staticmethod
    def load_file(file_path, file_type='text', default=None):
        """通用文件加载方法"""
        try:
            if not os.path.isabs(file_path):
                file_path = Config.get_full_path(file_path)
            
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return default
            
            if file_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return default
    
    @staticmethod
    def save_file(file_path, data, file_type='text'):
        """通用文件保存方法"""
        try:
            if not os.path.isabs(file_path):
                file_path = Config.get_full_path(file_path)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if file_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            return True
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
            return False

class CharacterLoader(BaseLoader):
    """加载角色设定"""
    
    @staticmethod
    def load_character(file_path=None):
        """从文件加载角色设定"""
        if file_path is None:
            file_path = Config.CHARACTER_FILE

        data = BaseLoader.load_file(file_path, 'json')
        if data is None or 'content' not in data:
            return "你是一个可爱的桌宠，性格活泼开朗，喜欢和主人互动。"
        return f"""你是一个桌宠角色，以下是你的设定：{data['content']}请根据以上设定进行对话，保持角色的一致性"""

class UserInfoLoader(BaseLoader):
    """加载用户信息"""
    
    def __init__(self, file_path=None):
        if file_path is None:
            file_path = Config.USER_INFO_FILE
        self.file_path = file_path
        self.info = self.load_info()
    
    def load_info(self):
        """从JSON文件加载用户信息"""
        return BaseLoader.load_file(self.file_path, 'json', {})
    
    def get_info_string(self):
        """获取格式化的用户信息字符串"""
        if not self.info:
            return ""
        
        info_map = {
            "nickname": "用户的昵称是：{}",
            "birthday": "用户的生日是：{}",
            "oc_name": "用户对角色的称呼是：{}",
            "relationship": "用户与角色的关系设定是：{}"
        }
        
        parts = [formatter.format(self.info[key]) for key, formatter in info_map.items() if self.info.get(key)]
        return " | ".join(parts)