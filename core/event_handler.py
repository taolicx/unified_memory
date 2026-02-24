"""
事件处理器 - 处理对话事件和记忆操作
"""
import logging
from typing import Optional
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.event.filter import event_message_type
from astrbot.api.message_components import Plain

from ..base import ConfigManager
from ..managers import MemoryEngine, ConversationManager

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
        # 注册群聊消息监听
        plugin.register_event_handler(
            event_message_type("group_message"),
            self.on_group_message
        )
        
        # 注册私聊消息监听
        plugin.register_event_handler(
            event_message_type("private_message"),
            self.on_private_message
        )
        
        logger.info("事件监听器已注册")

    async def on_group_message(self, event: AstrMessageEvent):
        """处理群聊消息"""
        await self._handle_message(event)

    async def on_private_message(self, event: AstrMessageEvent):
        """处理私聊消息"""
        await self._handle_message(event)

    async def _handle_message(self, event: AstrMessageEvent):
        """处理消息"""
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

    async def on_bot_response(self, event: AstrMessageEvent, response: str):
        """处理机器人响应"""
        try:
            session_id = event.get_session_id()
            persona_id = event.get_platform_name()
            
            # 添加机器人响应到会话
            await self.conversation_manager.add_message(
                session_id,
                "assistant",
                response,
                persona_id
            )
            
        except Exception as e:
            logger.error(f"处理机器人响应失败：{e}", exc_info=True)