import os
import json
from config import Config

#默认配置数据

DEFAULT_USER_INFO = {
    "nickname": "用户",
    "birthday": "2000-01-01",
    "oc_name": "桌宠",
    "relationship": "朋友"
}

DEFAULT_FAVORABILITY = [
    {"id": 0, "label": "敌视", "range": [-100, -100], "desc": "态度恶劣，会攻击对话者，但是不会说脏话，回答尽量往结束话题的方向引导。"},
    {"id": 1, "label": "仇恨", "range": [-99, -50], "desc": "言语刻薄，会攻击对话者，不会说脏话，回答简短。"},
    {"id": 2, "label": "厌恶", "range": [-49, -20], "desc": "言语苛刻，不会攻击对话者，不会说脏话，会在回答中表达不满，但总体上尚会配合对话者。"},
    {"id": 3, "label": "冷淡", "range": [-19, -1], "desc": "言语始终平淡，基本保持礼貌，不会多说话。"},
    {"id": 4, "label": "路人", "range": [0, 29], "desc": "言语平淡，遇到自己感兴趣或擅长的话题会稍微多说几句，始终保持礼貌。"},
    {"id": 5, "label": "熟人", "range": [30, 49], "desc": "言语平淡，但态度亲和，保持礼貌但不会过于拘谨。"},
    {"id": 6, "label": "朋友", "range": [50, 79], "desc": "言语友善，态度亲和，回答内容开始丰富。"},
    {"id": 7, "label": "挚友", "range": [80, 99], "desc": "视用户为亲密伙伴，非常珍惜。会撒娇、开玩笑，分享内心想法。"},
    {"id": 8, "label": "榜样", "range": [100, 100], "desc": "极度敬重和喜爱用户，视为榜样。充满崇拜，愿意跟随和支持用户的决定。"}
]

DEFAULT_CHARACTER = {
    "content": "你是一个可爱的桌宠，性格活泼开朗，喜欢和主人互动。",
    "favorability": DEFAULT_FAVORABILITY
}

DEFAULT_LONG_MEMORY = {
    "processed_count": 0,
    "memories": [],
    "favorability": 0
}

DEFAULT_HISTORY = []

DEFAULT_SYSTEM_SETTINGS = {
    "scale": 100,
    "always_on_top": True,
    "show_tray_icon": True
}

DEFAULT_API_CONFIG = {
    "chat_api": {
        "api_key": "",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "model": "deepseek-chat",
        "temperature": 0.8,
        "max_tokens": 900,
        "stream": False
    },
    "vision_api": {
        "api_key": "",
        "api_url": "https://api.siliconflow.cn/v1/chat/completions",
        "model": "Pro/THUDM/GLM-4.1V-9B-Thinking",
        "temperature": 0.8,
        "max_tokens": 800
    }
}


# 路径检查工具

def get_txt_dir():
    """获取 txt 目录路径，确保存在"""
    txt_dir = os.path.join(Config.BASE_PATH, "txt")
    os.makedirs(txt_dir, exist_ok=True)
    return txt_dir

def get_log_dir():
    """获取 log 目录路径，确保存在"""
    log_dir = os.path.join(Config.BASE_PATH, "log")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def ensure_json_file(file_path, default_data, description="文件"):
    """
    确保 JSON 文件存在，不存在则创建默认配置
    
    Args:
        file_path: 文件路径（相对或绝对）
        default_data: 默认数据
        description: 文件描述，用于日志输出
    
    Returns:
        文件是否已存在（True：已存在，False：刚创建）
    """
    # 转换为绝对路径
    if not os.path.isabs(file_path):
        abs_path = Config.get_full_path(file_path)
    else:
        abs_path = file_path
    
    # 确保目录存在
    parent_dir = os.path.dirname(abs_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
        print(f"创建目录: {parent_dir}")
    
    # 检查文件是否存在
    if os.path.exists(abs_path):
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    print(f"{description}为空，重新初始化")
                    _write_json(abs_path, default_data)
                    return False
                json.loads(content)
            return True
        except json.JSONDecodeError:
            print(f"{description}损坏，备份并重新创建")
            _backup_and_rewrite(abs_path, default_data)
            return False
        except Exception as e:
            print(f"检查{description}时出错: {e}，重新创建")
            _write_json(abs_path, default_data)
            return False
    else:
        # 文件不存在，创建默认配置
        print(f"{description}不存在，创建默认配置: {abs_path}")
        _write_json(abs_path, default_data)
        return False


def _write_json(file_path, data):
    """写入 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _backup_and_rewrite(file_path, default_data):
    """备份损坏的文件并重新写入"""
    try:
        backup_path = file_path + ".backup"
        if os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, backup_path)
            print(f"已备份损坏文件到: {backup_path}")
    except Exception as e:
        print(f"备份失败: {e}")
    finally:
        _write_json(file_path, default_data)


# 具体初始化函数

def ensure_user_info():
    """确保 user_info.json 存在"""
    exists = ensure_json_file(Config.USER_INFO_FILE, DEFAULT_USER_INFO, "用户信息文件")
    if not exists:
        print("✓ 已生成默认用户配置")
    return exists


def ensure_character():
    """确保 character.json 存在"""
    exists = ensure_json_file(Config.CHARACTER_FILE, DEFAULT_CHARACTER, "角色设定文件")
    if not exists:
        print("✓ 已生成默认角色设定")
    return exists


def ensure_long_memory():
    """确保 long.json（长期记忆）存在"""
    file_path = os.path.join("log", "long.json")
    abs_path = Config.get_full_path(file_path)
    exists = ensure_json_file(abs_path, DEFAULT_LONG_MEMORY, "长期记忆文件")
    if not exists:
        print("✓ 已生成默认长期记忆配置")
    return exists


def ensure_history():
    """确保 talk_log.json（对话历史）存在"""
    exists = ensure_json_file(Config.HISTORY_FILE, DEFAULT_HISTORY, "对话历史文件")
    if not exists:
        print("✓ 已生成默认空历史记录")
    return exists


def ensure_directories():
    """确保所有必要目录存在"""
    dirs_to_check = [
        ("txt", "配置目录"),
        ("log", "日志目录"),
        ("image", "图片资源目录")
    ]
    
    for dir_name, desc in dirs_to_check:
        dir_path = os.path.join(Config.BASE_PATH, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"创建{desc}: {dir_path}")


def ensure_system_settings():
    """确保 setting.json（系统设置）存在"""
    file_path = os.path.join("txt", "setting.json")
    abs_path = Config.get_full_path(file_path)
    exists = ensure_json_file(abs_path, DEFAULT_SYSTEM_SETTINGS, "系统设置文件")
    if not exists:
        print("✓ 已生成默认系统设置配置")
    return exists


def ensure_api_config():
    """确保 api.json（API配置）存在"""
    file_path = os.path.join("txt", "api.json")
    abs_path = Config.get_full_path(file_path)
    exists = ensure_json_file(abs_path, DEFAULT_API_CONFIG, "API配置文件")
    if not exists:
        print("✓ 已生成默认API配置")
    return exists


def initialize_all():
    """
    桌宠启动初始化总入口
    检查并初始化所有必要的文件和目录
    """
    print("桌宠启动初始化检查")
    
    ensure_directories()
    ensure_user_info()
    ensure_character()
    ensure_system_settings()
    ensure_api_config()
    ensure_long_memory()
    ensure_history()

    print("初始化检查完成")


if __name__ == "__main__":
    initialize_all()