import requests, os, json
from utils.config import Config
from utils.loader import UserInfoLoader

def load_api_config():
    """加载 api.json 配置"""
    api_file = Config.get_full_path(os.path.join("txt", "api.json"))
    with open(api_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_api_request(api_url, api_key, data):
    """发送API请求并统一处理错误"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "请求超时，请检查网络连接"
    except requests.exceptions.ConnectionError:
        return "网络连接失败，请检查网络"
    except requests.exceptions.HTTPError as e:
        error_map = {
            401: "API密钥错误，请检查您的API密钥",
            403: "API访问被拒绝，请检查权限设置",
            429: "请求过于频繁，请稍后再试"
        }
        return error_map.get(response.status_code, f"API请求失败: {response.status_code}")
    except Exception as e:
        return f"发生错误: {str(e)}"

def build_conversation_messages(base_prompt, user_info_loader, history_manager, 
                               user_content=None, new_role="user", memory_manager=None,
                               heart_manager=None):
    """构建完整的对话消息列表"""
    messages = [{"role": "system", "content": base_prompt}]
    
    if heart_manager:
        heart_desc = heart_manager.get_level_desc()
        if heart_desc:
            messages.append({
                "role": "system", 
                "content": f"【当前情感状态】{heart_desc}\n\n这是你对用户的真实情感基础和当前态度，后续回复必须严格遵循这个情感基调。"
            })
    
    user_info_str = user_info_loader.get_info_string()
    if user_info_str:
        user_info_msg = f"以下是重要用户档案信息，这对理解对话上下文至关重要：\n{user_info_str}"
        messages.append({"role": "system", "content": user_info_msg})
    
    if memory_manager:
        long_memory_str = memory_manager.get_long_memories_string()
        if long_memory_str:
            long_memory_msg = f"以下是长期核心记忆，这些是过去对话的重要总结：\n{long_memory_str}"
            messages.append({"role": "system", "content": long_memory_msg})
    
    system_messages_count = len(messages)
    
    if history_manager:
        for talk in history_manager.get_all_talks():
            role = "user" if talk["role"] in ["event", "user"] else "assistant"
            content = f"[互动事件] {talk['content']}" if talk["role"] == "event" else talk["content"]
            messages.append({"role": role, "content": content})
    
    if user_content is not None:
        messages.append({"role": new_role, "content": user_content})
    
    return messages, system_messages_count


class BaseAPI:
    """API基类"""
    
    def __init__(self, api_key, api_url, model, character_prompt=None, 
                 user_info_loader=None, history_manager=None, heart_manager=None):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.character_prompt = character_prompt or "你是一个可爱的桌宠，性格活泼开朗，喜欢和主人互动。"
        self.user_info_loader = user_info_loader or UserInfoLoader()
        self.history_manager = history_manager
        self.heart_manager = heart_manager

class DeepSeekAPI(BaseAPI):
    """DeepSeek API通信类"""
    
    def __init__(self, api_key=None, character_prompt=None, history_manager=None, 
                 memory_manager=None, heart_manager=None):
        api_config = load_api_config()
        chat_config = api_config["chat_api"]
        
        super().__init__(
            api_key=chat_config["api_key"],
            api_url=chat_config["api_url"],
            model=chat_config["model"],
            character_prompt=character_prompt,
            user_info_loader=UserInfoLoader(),
            history_manager=history_manager,
            heart_manager=heart_manager
        )
        self.temperature = chat_config["temperature"]
        self.max_tokens = chat_config["max_tokens"]
        self.stream = chat_config["stream"]
        self.memory_manager = memory_manager
        self._load_conversation()
    
    def _load_conversation(self):
        """加载对话历史到内存"""
        self.conversation_history, self._system_count = build_conversation_messages(
            self.character_prompt, 
            self.user_info_loader, 
            self.history_manager,
            memory_manager=self.memory_manager,
            heart_manager=self.heart_manager
        )
    
    def update_conversation_history(self):
        """更新内存中的对话历史"""
        self._load_conversation()
    
    def get_response(self, user_input):
        """获取AI回复"""
        self.conversation_history, self._system_count = build_conversation_messages(
            self.character_prompt,
            self.user_info_loader,
            self.history_manager,
            user_content=user_input,
            new_role="user",
            memory_manager=self.memory_manager,
            heart_manager=self.heart_manager
        )
        
        # 裁剪历史
        max_total = Config.MAX_HISTORY_MESSAGES + self._system_count
        if len(self.conversation_history) > max_total:
            self.conversation_history = (
                self.conversation_history[:self._system_count] + 
                self.conversation_history[-Config.MAX_HISTORY_MESSAGES:]
            )
        
        data = {
            "model": self.model,
            "messages": self.conversation_history,
            "stream": self.stream,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        ai_response = send_api_request(self.api_url, self.api_key, data)
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response


class VisionAPI(BaseAPI):
    """SiliconFlow视觉理解API"""
    
    def __init__(self, api_key=None, character_prompt=None, user_info_loader=None, 
                 history_manager=None, memory_manager=None, heart_manager=None):
        api_config = load_api_config()
        vision_config = api_config["vision_api"]
        
        super().__init__(
            api_key=vision_config["api_key"],
            api_url=vision_config["api_url"],
            model=vision_config["model"],
            character_prompt=character_prompt,
            user_info_loader=user_info_loader,
            history_manager=history_manager,
            heart_manager=heart_manager
        )
        self.temperature = vision_config["temperature"]
        self.max_tokens = vision_config["max_tokens"]
        self.memory_manager = memory_manager

    def analyze_screen(self, image_base64, custom_prompt=None):
        """分析屏幕截图并返回AI评价"""
        pure_base64 = image_base64.split(',', 1)[1] if image_base64.startswith('data:image') else image_base64
        
        system_content_parts = [f"【你的身份】{self.character_prompt}\n\n这是你的核心人设，后续描述必须用第一人称'我'，并保持这个性格语气。"]
        
        if self.heart_manager:
            heart_desc = self.heart_manager.get_level_desc()
            if heart_desc:
                system_content_parts.append(f"【当前情感状态】{heart_desc}\n\n这是你对用户的真实情感态度，观察屏幕时必须保持这个情感基调，用符合当前关系的态度描述看到的内容。")
        
        user_info_str = self.user_info_loader.get_info_string()
        if user_info_str:
            system_content_parts.append(f"【用户档案】{user_info_str}\n\n这是你需要记住的用户信息，观察屏幕时要联想用户的兴趣。")
        
        if self.memory_manager:
            long_memory_str = self.memory_manager.get_long_memories_string()
            if long_memory_str:
                system_content_parts.append(f"【过往记忆】{long_memory_str}\n\n这些是你和用户的共同回忆，描述画面时可以自然联系这些记忆。")
        
        history_context = ""
        if self.history_manager:
            recent_talks = self.history_manager.get_all_talks()[-20:]
            if recent_talks:
                history_parts = []
                for talk in recent_talks:
                    if talk["role"] == "event":
                        history_parts.append(f"\n- [事件] {talk['content']}")
                    elif talk["role"] == "user":
                        history_parts.append(f"\n- 用户说: {talk['content']}")
                    elif talk["role"] == "assistant":
                        history_parts.append(f"\n- 你回复: {talk['content']}")
                history_context = "【最近对话】" + "".join(history_parts) + "\n\n"
        
        system_content = "\n\n".join(system_content_parts)
        
        if custom_prompt is None:
            base_question = f"""{history_context}【任务】请观察这张屏幕截图：
- 看到了用户大概在进行什么活动（如浏览网页、写代码、玩游戏等）
回复：
- 符合人设的对画面进行的评价

【重要规则】
- 只描述画面里真实存在的内容，禁止编造
- 不确定就说"看不太清楚"
- 必须用符合桌宠人设的人称来描述，保持你的人设语气，并体现【当前情感状态】
- 内容准确精炼，但要体现你的性格特点和当前对用户的情感态度
- 可以参考历史记录进行回复，可以联系过往记忆
- 可以增加一些动作和表情细节，让回复更生动有趣（加在括号里）
- 一定要符合【你的身份】，对用户的认知符合【用户档案】和【当前情感状态】

请用简洁的语言对看到的画面进行简要的一到二句回复。"""
        else:
            base_question = custom_prompt
        
        messages = [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{pure_base64}"}},
                    {"type": "text", "text": base_question}
                ]
            }
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        return send_api_request(self.api_url, self.api_key, data)