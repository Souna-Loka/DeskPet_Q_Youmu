from PyQt5.QtCore import QTimer
from datetime import datetime
from threading import Thread
from api_client import send_api_request

class TimeAnnouncer:
    """整点报时器"""
    def __init__(self, talk_manager, api, heart_manager=None):
        self.tm = talk_manager
        self.api = api
        self.heart_manager = heart_manager
        self.pending_msg = None
        self.last_hour = datetime.now().hour
        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(1000)
    
    def check(self):
        now = datetime.now()
        # 提前触发API请求
        if now.minute == 59 and now.second == 30 and now.hour != self.last_hour:
            self.last_hour = now.hour
            next_hour = (now.hour + 1) % 24
            Thread(target=self._fetch_ai_response, args=(next_hour,), daemon=True).start()
        
        # 整点显示已准备好的回复
        elif now.minute == 0 and now.second == 0 and self.pending_msg:
            self.tm.show_bubble(self.pending_msg)
            
            if hasattr(self.tm, 'history_manager') and self.tm.history_manager:
                self.tm.history_manager.add_talk("assistant", self.pending_msg)
            self.pending_msg = None
    
    def _fetch_ai_response(self, hour):
        """在后台线程获取AI整点报时回复"""
        try:
            system_parts = []
            
            if hasattr(self.api, 'character_prompt') and self.api.character_prompt:
                system_parts.append(f"【你的身份】{self.api.character_prompt}\n\n这是你的核心人设，你必须用第一人称'我'，保持这个性格语气。")
            
            if self.heart_manager:
                heart_desc = self.heart_manager.get_level_desc()
                if heart_desc:
                    system_parts.append(f"【当前情感状态】{heart_desc}\n\n这是你对用户的真实情感态度，报时时必须符合这个情感基调，用符合当前关系亲密度的语气提醒用户。")
            
            if hasattr(self.api, 'user_info_loader') and self.api.user_info_loader:
                user_info_str = self.api.user_info_loader.get_info_string()
                if user_info_str:
                    system_parts.append(f"【用户档案】{user_info_str}\n\n这是你需要记住的用户信息，报时时结合用户的作息、习惯或喜好会让提醒更贴心。")
            
            if hasattr(self.api, 'memory_manager') and self.api.memory_manager:
                long_memory_str = self.api.memory_manager.get_long_memories_string()
                if long_memory_str:
                    system_parts.append(f"【过往记忆】{long_memory_str}\n\n这些是你和用户的共同回忆，报时时可以自然联系这些记忆，让对话更有连贯性。")
            
            system_content = "\n\n".join(system_parts)
            
            history_context = ""
            if hasattr(self.api, 'history_manager') and self.api.history_manager:
                recent_talks = self.api.history_manager.get_all_talks()[-5:]
                if recent_talks:
                    history_parts = []
                    for talk in recent_talks:
                        if talk["role"] == "event":
                            history_parts.append(f"[事件] {talk['content']}")
                        elif talk["role"] == "user":
                            history_parts.append(f"用户说: {talk['content']}")
                        elif talk["role"] == "assistant":
                            history_parts.append(f"你回复: {talk['content']}")
                    if history_parts:
                        history_context = "【最近对话】" + "\n".join(history_parts) + "\n\n"
            
            user_content = f"""{history_context}【准点报时】现在是{hour}:00，到了整点报时的时间。

请结合以上信息，用符合你人设和【当前情感状态】的语气提醒主人现在的时间。

【要求】
1. 必须用第一人称"我"，保持性格、人设和当前情感状态的一致性
2. 结合用户档案中的信息（如昵称、关系）个性化提醒
3. 参考之前的对话上下文，让报时自然融入交流节奏，不要突兀
4. 根据具体时间（早晨/中午/晚上/深夜）给出相应的温馨关怀或提醒
5. 可以关联过往记忆让对话更连贯（如"记得你昨天这个时间..."）
6. 简短自然，30字以内，不要加引号或"报时："等标签
7. 如果刚好赶上饭点、休息时间等，可以给出相应建议
8. 回复必须体现【当前情感状态】中描述的态度和语气

直接输出你要对主人说的话："""

            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ]
            
            data = {
                "model": self.api.model,
                "messages": messages,
                "stream": False,
                "temperature": 0.8,
                "max_tokens": 100
            }
            
            response = send_api_request(self.api.api_url, self.api.api_key, data)
            
            if response:
                self.pending_msg = response.strip().strip('"').strip("“”")
            else:
                self.pending_msg = f"现在是{hour}点了哦~"
                
        except Exception as e:
            print(f"准点报时生成失败: {e}")
            self.pending_msg = f"现在是{hour}点了哦~"