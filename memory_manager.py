import json
import os
from datetime import datetime
from threading import Lock, Thread
from config import Config
from api_client import DeepSeekAPI

class MemoryManager:
    """短期和长期记忆管理器 """
    
    def __init__(self, history_manager, api_key=None):
        """初始化记忆管理器"""
        self.history_manager = history_manager
        self.api_key = api_key
        self.long_memory_file = "log/long.json"
        self.lock = Lock()
        
        # 加载长期记忆数据
        self.load_long_memory()
        
        # 启动时检查是否需要整理
        self.check_and_consolidate()
    
    def load_long_memory(self):
        """
        加载长期记忆文件
        """
        try:
            # 获取绝对路径
            abs_path = Config.get_full_path(self.long_memory_file)
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_count = data.get("processed_count", 0)
                    self.long_memories = data.get("memories", [])
            else:
                # 初始化新文件
                self.processed_count = 0
                self.long_memories = []
                self.save_long_memory()
        except Exception as e:
            print(f"加载长期记忆失败: {e}，初始化空数据")
            self.processed_count = 0
            self.long_memories = []
    
    def save_long_memory(self):
        """保存长期记忆到文件"""
        try:
            abs_path = Config.get_full_path(self.long_memory_file)
            data = {}
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = {}
            data["processed_count"] = self.processed_count
            data["memories"] = self.long_memories
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存长期记忆失败: {e}")
    
    def get_unprocessed_count(self):
        """
        获取未处理的消息数量
        
        Returns:
            int: 未处理的消息数量
        """
        total_messages = len(self.history_manager.get_all_talks())
        return max(0, total_messages - self.processed_count)
    
    def should_consolidate(self):
        """
        判断是否需要整理短期记忆
        
        Returns:
            bool: 当未处理消息数达到MAX_HISTORY_MESSAGES时返回True
        """
        return self.get_unprocessed_count() >= Config.MAX_HISTORY_MESSAGES
    
    def check_and_consolidate(self):
        """
        检查并触发记忆整理
        
        如果满足整理条件，在后台线程执行整理，避免阻塞UI
        """
        if self.should_consolidate():
            print(f"检测到{self.get_unprocessed_count()}条未处理消息，触发记忆整理...")
            Thread(target=self._consolidate_in_background, daemon=True).start()
    
    def _consolidate_in_background(self):
        """在后台执行记忆整理"""
        try:
            self.consolidate_short_term_memory()
        except Exception as e:
            print(f"记忆整理失败: {e}")
    
    def consolidate_short_term_memory(self):
        """
        整理短期记忆为长期记忆
        
        流程：
        1. 获取未处理的短期记忆
        2. 调用DeepSeek API提炼核心内容
        3. 将提炼结果存入long.json
        4. 更新processed_count
        5. 当长期记忆满20条时，压缩至5-10条
        """
        with self.lock:
            batch_count = 0  # 记录处理批次
            
            # 使用循环替代递归，持续处理直到没有未整理内容
            while self.should_consolidate():
                batch_count += 1
                remaining = self.get_unprocessed_count()
                print(f"\n[记忆整理] 第{batch_count}批开始 → 剩余{remaining}条待整理")
                # 获取未处理的消息
                all_talks = self.history_manager.get_all_talks()
                unprocessed = all_talks[self.processed_count:self.processed_count + Config.MAX_HISTORY_MESSAGES]
                if not unprocessed:
                    print("[记忆整理] 未找到可处理的消息，退出循环")
                    break          
                print(f"[记忆整理] 正在处理第{self.processed_count}到{self.processed_count + len(unprocessed)}条消息...")            
                # 构建用于提炼的文本
                memory_text = self._build_memory_text(unprocessed)
                print(f"[记忆整理] 构建的文本长度: {len(memory_text)} 字符")            
                # 调用API提炼核心记忆
                consolidated_memory = self._call_deepseek_for_consolidation(memory_text)
                if consolidated_memory:
                    # 添加到长期记忆
                    new_memory_id = len(self.long_memories)
                    self.long_memories.append({
                        "id": new_memory_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "content": consolidated_memory,
                        "source_count": len(unprocessed)
                    })
                    
                    # 更新已处理数量
                    self.processed_count += len(unprocessed)
                    
                    print(f"[记忆整理] ✓ 成功整理为记忆ID:{new_memory_id} - {consolidated_memory}")
                    print(f"[记忆整理] 已处理总数: {self.processed_count}, 长期记忆数: {len(self.long_memories)}")
                    
                    # 检查是否需要压缩长期记忆（满20条时）
                    if len(self.long_memories) >= 20:
                        print("[记忆整理] 长期记忆达到20条，触发压缩...")
                        self.compress_long_term_memories()
                    self.save_long_memory()
                    remaining_after = self.get_unprocessed_count()
                    if remaining_after > 0:
                        print(f"[记忆整理] 检测到还有{remaining_after}条未处理，继续下一轮循环...")
                    else:
                        print("[记忆整理] 所有消息已整理完毕")
                else:
                    print("[记忆整理] ✗ API提炼失败，跳过并终止整理")
                    break
            
            if batch_count == 0:
                print("[记忆整理] 未达到整理条件，无需处理")
            else:
                print(f"\n[记忆整理] 总计完成{batch_count}批整理，最终长期记忆数: {len(self.long_memories)}")
    
    def _build_memory_text(self, talks):
        """
        构建用于提炼的文本
        
        Args:
            talks: 短期记忆对话列表
            
        Returns:
            str: 格式化后的文本
        """
        lines = []
        for talk in talks:
            role = talk["role"]
            content = talk["content"]
            if role == "event":
                lines.append(f"[事件] {content}")
            elif role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"桌宠: {content}")
        
        return "\n".join(lines)
    
    def _call_deepseek_for_consolidation(self, memory_text):
        """
        调用DeepSeek API提炼核心记忆
        
        Args:
            memory_text: 原始对话文本
            
        Returns:
            str: 提炼后的核心记忆（≤15字），失败返回空字符串
        """
        try:
            prompt = f"""请将以下对话记录提炼成一条核心记忆，要求：
                        1. 只保留值得长期记忆的重要信息
                        2. 不超过15个字
                        3. 语言凝练，没有冗余词语
                        4. 以第三人称客观描述

对话记录：
{memory_text}

请直接输出提炼后的核心记忆，不要有任何解释或附加内容。"""
            
            # 临时API实例（不使用历史记录）
            temp_api = DeepSeekAPI(
                api_key=self.api_key,
                character_prompt="你是一个高效的信息提炼助手，擅长提取核心要点。",
                history_manager=None
            )
            
            response = temp_api.get_response(prompt)
            
            # 清理响应
            memory = response.strip()
            
            # 验证长度
            if len(memory) > 15:
                print(f"警告：提炼的记忆超过15字限制（{len(memory)}字），将截断")
                memory = memory[:15]
            
            return memory
        except Exception as e:
            print(f"调用DeepSeek API失败: {e}")
            return ""
    
    def compress_long_term_memories(self):
        """
        压缩长期记忆
        """
        print("长期记忆达到20条，触发压缩...")
        
        if len(self.long_memories) < 20:
            return
        
        # 构建所有长期记忆的文本
        all_memories_text = "\n".join([f"{i+1}. {m['content']}" for i, m in enumerate(self.long_memories)])
        
        try:
            prompt = f"""请将以下20条长期记忆进一步压缩提炼，要求：
1. 保留最重要、最核心的事件和信息
2. 提炼成5-10条记忆
3. 每条不超过15个字
4. 删除重复、次要或已过时的记忆
5. 以编号列表形式输出

现有记忆：
{all_memories_text}

请直接输出提炼后的核心记忆列表，不要有任何解释或附加内容。"""
            
            temp_api = DeepSeekAPI(
                api_key=self.api_key,
                character_prompt="你是一个高效的信息压缩助手，擅长提取核心要点。",
                history_manager=None
            )
            
            response = temp_api.get_response(prompt)
            
            # 解析响应
            new_memories = []
            for line in response.strip().split('\n'):
                line = line.strip()
                # 去除编号
                if '.' in line:
                    line = line.split('.', 1)[1].strip()
                if line and len(line) <= 15:
                    new_memories.append(line)
            
            # 验证数量
            if 5 <= len(new_memories) <= 10:
                # 替换旧记忆
                self.long_memories = []
                for i, content in enumerate(new_memories):
                    self.long_memories.append({
                        "id": i,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "content": content,
                        "source_count": 0  # 压缩后的记忆不记录源数量
                    })
                print(f"成功压缩长期记忆：{len(self.long_memories)}条")
            else:
                print(f"警告：压缩后的记忆数量不符合要求（{len(new_memories)}条），跳过压缩")
        
        except Exception as e:
            print(f"压缩长期记忆失败: {e}")
    
    def get_long_memories_string(self):
        """
        获取长期记忆字符串（用于API调用）
        
        Returns:
            str: 格式化的长期记忆文本
        """
        if not self.long_memories:
            return ""
        
        parts = [f"- {m['content']}" for m in self.long_memories]
        return "长期核心记忆：\n" + "\n".join(parts)