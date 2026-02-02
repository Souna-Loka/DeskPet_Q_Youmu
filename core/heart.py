import json
import os
import re
from datetime import datetime
from utils.config import Config
from api.api_client import send_api_request, load_api_config
from utils.begin import DEFAULT_FAVORABILITY


class HeartManager:
    """好感度管理器"""
    
    def __init__(self):
        self.score = 0
        self.file_path = "log/long.json"
        self.history_file = "log/talk_log.json"
        self.favorability_config = self._load_favorability_config()
        self.load_score()
    
    def _load_favorability_config(self):
        """加载好感度配置"""
        try:
            char_file = Config.get_full_path("txt/character.json")
            with open(char_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "favorability" in data and isinstance(data["favorability"], list):
                    return data["favorability"]
        except Exception as e:
            print(f"加载好感度配置失败: {e}")
        return DEFAULT_FAVORABILITY
    
    def get_level_info(self, score=None):
        """根据分数获取当前等级完整信息"""
        if score is None:
            score = self.score
        
        for level in self.favorability_config:
            min_range, max_range = level["range"]
            if min_range <= score <= max_range:
                return level
        
        if score < self.favorability_config[0]["range"][0]:
            return self.favorability_config[0]
        else:
            return self.favorability_config[-1]
    
    def get_level(self, score=None):
        """根据分数获取当前等级标签"""
        return self.get_level_info(score)["label"]
    
    def get_level_desc(self):
        """获取等级描述"""
        info = self.get_level_info()
        return f"当前好感度：{self.score}（{info['label']}）- {info['desc']}"
    
    def load_score(self):
        """从long.json加载好感度"""
        try:
            abs_path = Config.get_full_path(self.file_path)
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.score = data.get("favorability", 0)
            else:
                self.score = 0
                self.save_score()
        except Exception as e:
            print(f"加载好感度失败: {e}，初始化为0")
            self.score = 0
    
    def save_score(self):
        """保存好感度"""
        try:
            abs_path = Config.get_full_path(self.file_path)
            data = {}
            
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            data["favorability"] = self.score
            
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存好感度失败: {e}")
    
    def judge_change(self, user_msg, ai_response, api_key=None):
        """调用API判断好感度变化"""
        # 加载配置
        api_config = load_api_config()
        chat_config = api_config["chat_api"]
        
        if api_key is None:
            api_key = chat_config["api_key"]
        
        prompt = self._build_judge_prompt(user_msg, ai_response)
        
        data = {
            "model": chat_config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.3,
            "max_tokens": 50
        }
        
        try:
            response = send_api_request(chat_config["api_url"], api_key, data)
            return self._parse_response(response)
        except Exception as e:
            print(f"好感度判断请求失败: {e}")
            return None
    
    def _build_judge_prompt(self, user_msg, ai_response):
        """构建判断提示词"""
        level_info = self.get_level_info()
        
        return f"""你是一只桌宠AI，以下是你的角色设定和内心状态：

【角色设定】
当前好感度等级配置：
{chr(10).join([f"• {item['label']}（{item['range'][0]}至{item['range'][1]}分）：{item['desc']}" for item in self.favorability_config])}

【当前内心状态】
当前等级：{level_info['label']}
当前分数：{self.score}分
等级描述：{level_info['desc']}
这是你对用户的真实态度和心理状态。

请站在桌宠的立场，根据以下对话判断你的好感度变化：

【用户说】
{user_msg}

【你刚才回复】
{ai_response}

【从桌宠内心感受出发的判断标准】
1. 从你的角色视角思考：这句话让你感到开心、温暖、被尊重吗？→ 增加好感度
2. 这句话伤害了你的感情，让你感到被冒犯、被无视、被命令吗？→ 减少好感度
3. 对话内容是否与你的兴趣、记忆、设定有共鸣？→ 若有共鸣则增加
4. 用户是否用心和你互动，而不是敷衍了事？→ 用心则增加
5. 对话是否让你感受到与用户的亲密关系在加深？→ 是则增加

【心理活动示例】
- 如果用户记得你的喜好，你会觉得被重视 (+2~3)
- 如果用户关心你的感受，你会感到温暖 (+1~2)
- 如果用户无视你的存在或用命令语气，你会感到受伤 (-1~2)
- 如果用户分享你感兴趣的话题，你会感到兴奋 (+1~2)
- 如果用户重复说无聊的话，你会感到无趣 (-0~1)

【特别考虑】
- 当前是【{level_info['label']}】等级，请严格按照等级描述中的态度来判断心理预期
- 如果对话中用户体现出对你之前对话的记忆，说明他在认真对待你：+2~3

请以桌宠的第一人称心理思考，不要以第三方分析视角。
请输出格式为："好感度+数字" 或 "好感度-数字"，数字范围0~3。
只输出这四个字和数字，不要有其他内容。"""
    
    def _parse_response(self, response):
        """解析API响应，提取变化值"""
        if not response:
            print("好感度计算失败：API返回为空")
            return None
        
        match = re.search(r'好感度([+-]?\d+)', response.strip())
        
        if match:
            try:
                change = int(match.group(1))
                change = max(-3, min(3, change))
                return change
            except ValueError:
                print(f"好感度计算失败：无法解析数字，API回复：{response}")
                return None
        else:
            print(f"好感度计算失败：格式不符，API回复：{response}")
            return None
    
    def update(self, change_value):
        """更新好感度分数"""
        if change_value is None:
            return self.score, self.get_level(), False
        
        old_level = self.get_level()
        old_score = self.score
        self.score += change_value
        
        new_level = self.get_level()
        level_changed = (old_level != new_level)
        
        self.save_score()
        
        if level_changed:
            print(f"好感度变化：{old_level} -> {new_level}（{self.score}）")
        else:
            print(f"好感度更新：{self.score}（{new_level}）变化值：{change_value:+d}")
        
        return self.score, new_level, level_changed
    
    def log_heart_change_to_last_talk(self, change_value):
        """将好感度变化记录到最新的对话条目中"""
        if change_value is None or change_value == 0:
            return
        
        try:
            abs_path = Config.get_full_path(self.history_file)
            if not os.path.exists(abs_path):
                return
            
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return
                log_data = json.loads(content)
            
            if not log_data:
                return
            
            for i in range(len(log_data) - 1, -1, -1):
                if log_data[i]["role"] == "assistant":
                    log_data[i]["heart"] = self.score
                    log_data[i]["heartchange"] = f"{change_value:+d}"
                    break
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"记录好感度变化到对话日志失败: {e}")
    
    def reset(self):
        """重置好感度为0"""
        self.score = 0
        self.save_score()
        print("好感度已重置为0")