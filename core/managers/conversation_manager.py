"""
会话管理器 - 管理对话会话和记忆上下文
"""
import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from ..base import ConfigManager
from .memory_engine import MemoryEngine

logger = logging.getLogger("astrbot_plugin_unified_memory")


class ConversationManager:
    """会话管理器"""

    def __init__(self, memory_engine: MemoryEngine):
        self.memory_engine = memory_engine
        self.config = memory_engine.config
        self._sessions: Dict[str, "SessionContext"] = {}
        self._lock = asyncio.Lock()

    def get_session(self, session_id: str) -> "SessionContext":
        """获取或创建会话上下文"""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(
                session_id,
                self.config.get_short_term_config()
            )
        return self._sessions[session_id]

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        persona_id: Optional[str] = None
    ) -> bool:
        """添加消息到会话"""
        session = self.get_session(session_id)
        await session.add_message(role, content)
        
        # 检查是否需要总结
        short_term_config = self.config.get_short_term_config()
        if short_term_config.get("enabled", True):
            if session.message_count >= short_term_config.get("summary_threshold", 10):
                await self._trigger_summary(session_id, persona_id)
        
        return True

    async def _trigger_summary(
        self,
        session_id: str,
        persona_id: Optional[str] = None
    ):
        """触发对话总结"""
        session = self.get_session(session_id)
        messages = session.get_messages()
        
        if len(messages) < 2:
            return
        
        try:
            # 总结并存储
            await self.memory_engine.summarize_and_store(
                session_id,
                messages,
                persona_id
            )
            
            # 清空短期记忆
            session.clear_messages()
            
            logger.info(f"会话 {session_id} 已总结并清空")
        
        except Exception as e:
            logger.error(f"总结会话失败：{e}")

    async def get_context(
        self,
        session_id: str,
        include_short_term: bool = True,
        include_long_term: bool = True,
        long_term_k: int = 5
    ) -> Dict[str, Any]:
        """获取会话上下文（用于注入到对话）"""
        session = self.get_session(session_id)
        context = {
            "session_id": session_id,
            "short_term": [],
            "long_term": [],
            "message_count": session.message_count
        }
        
        # 获取短期记忆
        if include_short_term:
            short_term_memories = await self.memory_engine.get_short_term_memories(
                session_id,
                limit=20
            )
            context["short_term"] = [m["content"] for m in short_term_memories]
        
        # 获取长期记忆（当前会话）
        if include_long_term:
            long_term_config = self.config.get_long_term_config()
            top_k = long_term_config.get("top_k", long_term_k)
            
            long_term_memories = await self.memory_engine.get_long_term_memories(
                session_id=session_id,
                limit=top_k
            )
            context["long_term"] = [
                {
                    "content": m["content"],
                    "canonical": m.get("canonical_summary", ""),
                    "persona": m.get("persona_summary", "")
                }
                for m in long_term_memories
            ]
        
        return context

    async def clear_session(self, session_id: str) -> bool:
        """清除会话记忆"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        # 清除数据库中的短期记忆
        await self.memory_engine.clear_short_term_memories(session_id)
        
        logger.info(f"会话 {session_id} 已清除")
        return True

    async def get_all_sessions(self) -> List[str]:
        """获取所有会话 ID"""
        return list(self._sessions.keys())

    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """清理不活跃的会话"""
        now = datetime.now()
        to_remove = []
        
        for session_id, session in self._sessions.items():
            if session.last_active:
                age = (now - session.last_active).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(session_id)
        
        for session_id in to_remove:
            del self._sessions[session_id]
            logger.debug(f"清理不活跃会话：{session_id}")
        
        return len(to_remove)


class SessionContext:
    """会话上下文"""

    def __init__(self, session_id: str, config: Dict[str, Any]):
        self.session_id = session_id
        self.max_messages = config.get("max_messages", 50)
        self._messages: Deque[Dict[str, str]] = deque(maxlen=self.max_messages)
        self.message_count = 0
        self.created_at = datetime.now()
        self.last_active = datetime.now()

    async def add_message(self, role: str, content: str):
        """添加消息"""
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.message_count += 1
        self.last_active = datetime.now()

    def get_messages(self) -> List[Dict[str, str]]:
        """获取所有消息"""
        return list(self._messages)

    def clear_messages(self):
        """清空消息（保留最近几条）"""
        # 保留最近 2 条用于上下文连贯
        recent = list(self._messages)[-2:]
        self._messages.clear()
        for msg in recent:
            self._messages.append(msg)
        self.message_count = len(recent)

    def get_recent_messages(self, n: int = 10) -> List[Dict[str, str]]:
        """获取最近 n 条消息"""
        return list(self._messages)[-n:]
