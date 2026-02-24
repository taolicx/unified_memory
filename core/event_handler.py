"""
事件处理器 - 处理对话事件和记忆操作
"""
import logging
from typing import Optional
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Plain

from .base import ConfigManager
from .managers import MemoryEngine, ConversationManager

logger = logging.getLogger("astrbot_plugin_unified_memory")


class EventHandler:
    """事件处理器"""

    def __init__(
        self,
        memory_engine: MemoryEngine,
        conversation_manager: ConversationManager,
        config: ConfigManager
    ):
        self.memory_engine = memory_engine
        self.conversation_manager = conversation_manager
        self.config = config

    def register_events(self, plugin):
        """注册事件监听器"""
        # 使用通用的 message 事件类型，兼容所有平台
        plugin.register_event_handler(
            "on_message",
            self.on_message
        )
        
        logger.info("事件监听器已注册")

    async def on_message(self, event: AstrMessageEvent):
        """处理所有消息"""
        try:
            # 获取会话 ID
            session_id = event.get_session_id()
            persona_id = event.get_platform_name()
            
            # 获取消息内容
            message_text = ""
            for comp in event.message_obj.message:
                if isinstance(comp, Plain):
                    message_text += comp.text
            
            if not message_text.strip():
                return
            
            # 获取发送者角色
            role = "user"  # 用户消息
            
            # 添加到会话
            await self.conversation_manager.add_message(
                session_id,
                role,
                message_text,
                persona_id
            )
            
            # 检查是否需要检索记忆
            await self._check_and_retrieve_memory(event, session_id, message_text)
            
        except Exception as e:
            logger.error(f"处理消息失败：{e}", exc_info=True)

    async def _check_and_retrieve_memory(
        self,
        event: AstrMessageEvent,
        session_id: str,
        message_text: str
    ):
        """检查并检索相关记忆"""
        long_term_config = self.config.get_long_term_config()
        
        if not long_term_config.get("auto_retrieve", True):
            return
        
        # 检索相关记忆
        top_k = long_term_config.get("top_k", 3)
        memories = await self.memory_engine.search_memories(message_text, top_k)
        
        if memories:
            # 将记忆注入到上下文（这里可以根据需要调整注入方式）
            memory_context = "\n".join([
                f"- {m.get('canonical_summary', m['content'])}"
                for m in memories[:top_k]
            ])
            
            # 存储记忆上下文供后续使用
            event.set_extra("retrieved_memories", memory_context)
            logger.debug(f"检索到 {len(memories)} 条相关记忆")