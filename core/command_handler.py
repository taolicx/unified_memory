"""
命令处理器 - 处理用户命令
"""
import logging
from typing import Optional, List
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Plain

from .base import ConfigManager, COMMAND_PREFIX, HELP_MESSAGE
from .managers import MemoryEngine, ConversationManager

logger = logging.getLogger("astrbot_plugin_unified_memory")


class CommandHandler:
    """命令处理器"""

    def __init__(
        self,
        memory_engine: MemoryEngine,
        conversation_manager: ConversationManager,
        config: ConfigManager
    ):
        self.memory_engine = memory_engine
        self.conversation_manager = conversation_manager
        self.config = config

    def register_commands(self, plugin):
        """注册命令"""
        # 使用统一的命令前缀注册，避免与 AstrBot 命令系统冲突
        # 注册帮助命令
        plugin.register_command(["umem", "umem_help"], self.cmd_help)
        
        # 注册状态命令
        plugin.register_command(["umem_status", "umem status"], self.cmd_status)
        
        # 注册短期记忆命令
        plugin.register_command(["umem_short", "umem short"], self.cmd_short_term)
        
        # 注册长期记忆命令
        plugin.register_command(["umem_long", "umem long"], self.cmd_long_term)
        
        # 注册搜索命令
        plugin.register_command(["umem_search", "umem search"], self.cmd_search)
        
        # 注册编辑命令
        plugin.register_command(["umem_edit", "umem edit"], self.cmd_edit)
        
        # 注册删除命令
        plugin.register_command(["umem_delete", "umem delete"], self.cmd_delete)
        
        # 注册清除命令
        plugin.register_command(["umem_clear", "umem clear"], self.cmd_clear)
        
        # 注册 WebUI 命令
        plugin.register_command(["umem_webui", "umem webui"], self.cmd_webui)
        
        logger.info("命令已注册")

    async def cmd_help(self, event: AstrMessageEvent) -> Optional[MessageChain]:
        """显示帮助信息"""
        help_text = HELP_MESSAGE.format(prefix=COMMAND_PREFIX)
        return MessageChain([Plain(help_text)])

    async def cmd_status(self, event: AstrMessageEvent) -> Optional[MessageChain]:
        """显示记忆库状态"""
        try:
            stats = await self.memory_engine.get_stats()
            
            status_text = f"""📊 记忆库状态

短期记忆：{stats.get('short_term_count', 0)} 条
长期记忆：{stats.get('long_term_count', 0)} 条
会话数量：{stats.get('session_count', 0)} 个

检索器状态:
- BM25 文档：{stats.get('retrieval', {}).get('bm25_count', 0)} 条
- 向量索引：{stats.get('retrieval', {}).get('vector_count', 0)} 条

系统状态：{'✅ 已初始化' if stats.get('initialized') else '❌ 未初始化'}
"""
            return MessageChain([Plain(status_text)])
        
        except Exception as e:
            logger.error(f"获取状态失败：{e}")
            return MessageChain([Plain(f"❌ 获取状态失败：{e}")])

    async def cmd_short_term(
        self,
        event: AstrMessageEvent,
        session_id: Optional[str] = None
    ) -> Optional[MessageChain]:
        """显示短期记忆"""
        try:
            if not session_id:
                session_id = event.get_session_id()
            
            memories = await self.memory_engine.get_short_term_memories(
                session_id,
                limit=20
            )
            
            if not memories:
                return MessageChain([Plain("暂无短期记忆")])
            
            text = f"📝 短期记忆 (会话：{session_id[:8]}...)\n\n"
            for i, m in enumerate(memories[:10], 1):
                content = m["content"][:50] + "..." if len(m["content"]) > 50 else m["content"]
                text += f"{i}. {content}\n"
            
            if len(memories) > 10:
                text += f"\n... 还有 {len(memories) - 10} 条"
            
            return MessageChain([Plain(text)])
        
        except Exception as e:
            logger.error(f"获取短期记忆失败：{e}")
            return MessageChain([Plain(f"❌ 获取失败：{e}")])

    async def cmd_long_term(
        self,
        event: AstrMessageEvent,
        query: Optional[str] = None
    ) -> Optional[MessageChain]:
        """显示/搜索长期记忆"""
        try:
            if query:
                # 搜索记忆
                memories = await self.memory_engine.search_memories(query, k=10)
            else:
                # 获取当前会话记忆
                session_id = event.get_session_id()
                memories = await self.memory_engine.get_long_term_memories(
                    session_id=session_id,
                    limit=20
                )
            
            if not memories:
                return MessageChain([Plain("暂无长期记忆")])
            
            text = f"📚 长期记忆"
            if query:
                text += f" (搜索：{query})"
            text += "\n\n"
            
            for i, m in enumerate(memories[:10], 1):
                content = m.get("canonical_summary", m["content"])
                content = content[:60] + "..." if len(content) > 60 else content
                score = m.get("score", "")
                score_text = f" (匹配度：{score:.2f})" if score else ""
                text += f"{i}. [{m['id']}]{content}{score_text}\n"
            
            if len(memories) > 10:
                text += f"\n... 还有 {len(memories) - 10} 条"
            
            return MessageChain([Plain(text)])
        
        except Exception as e:
            logger.error(f"获取长期记忆失败：{e}")
            return MessageChain([Plain(f"❌ 获取失败：{e}")])

    async def cmd_search(
        self,
        event: AstrMessageEvent,
        query: str,
        k: int = 10
    ) -> Optional[MessageChain]:
        """搜索记忆"""
        if not query:
            return MessageChain([Plain("❌ 请提供搜索关键词")])
        
        return await self.cmd_long_term(event, query)

    async def cmd_edit(
        self,
        event: AstrMessageEvent,
        memory_id: int,
        content: str
    ) -> Optional[MessageChain]:
        """编辑记忆"""
        try:
            if not memory_id or not content:
                return MessageChain([Plain("❌ 用法：/umem edit <id> <内容>")])
            
            await self.memory_engine.update_long_term_memory(
                memory_id,
                content=content
            )
            
            return MessageChain([Plain(f"✅ 记忆 {memory_id} 已更新")])
        
        except Exception as e:
            logger.error(f"编辑记忆失败：{e}")
            return MessageChain([Plain(f"❌ 编辑失败：{e}")])

    async def cmd_delete(
        self,
        event: AstrMessageEvent,
        memory_id: int
    ) -> Optional[MessageChain]:
        """删除记忆"""
        try:
            if not memory_id:
                return MessageChain([Plain("❌ 用法：/umem delete <id>")])
            
            await self.memory_engine.delete_long_term_memory(memory_id)
            
            return MessageChain([Plain(f"✅ 记忆 {memory_id} 已删除")])
        
        except Exception as e:
            logger.error(f"删除记忆失败：{e}")
            return MessageChain([Plain(f"❌ 删除失败：{e}")])

    async def cmd_clear(
        self,
        event: AstrMessageEvent,
        confirm: Optional[str] = None
    ) -> Optional[MessageChain]:
        """清除当前会话记忆"""
        try:
            session_id = event.get_session_id()
            
            if confirm != "confirm":
                return MessageChain([
                    Plain(f"⚠️ 确定要清除会话 {session_id[:8]}... 的所有记忆吗？\n")
                ])
            
            # 清除短期记忆
            await self.memory_engine.clear_short_term_memories(session_id)
            
            # 清除会话上下文
            await self.conversation_manager.clear_session(session_id)
            
            return MessageChain([Plain("✅ 会话记忆已清除")])
        
        except Exception as e:
            logger.error(f"清除记忆失败：{e}")
            return MessageChain([Plain(f"❌ 清除失败：{e}")])

    async def cmd_webui(self, event: AstrMessageEvent) -> Optional[MessageChain]:
        """显示 WebUI 信息"""
        try:
            webui_config = self.config.get_webui_config()
            host = webui_config.get("host", "127.0.0.1")
            port = webui_config.get("port", 8080)
            enabled = webui_config.get("enabled", True)
            
            if not enabled:
                return MessageChain([Plain("❌ WebUI 未启用")])
            
            # 尝试获取实际端口（如果已启动）
            actual_url = None
            if hasattr(self.memory_engine, 'webui_app') and self.memory_engine.webui_app:
                actual_url = await self.memory_engine.webui_app.get_actual_url()
            
            url = actual_url or f"http://{host}:{port}"
            
            text = f"""🌐 WebUI 管理面板

访问地址：{url}

功能:
- 查看所有记忆（短期/长期）
- 编辑、删除记忆
- 搜索记忆
- 记忆统计分析
- 导入/导出记忆

提示：如果端口被占用，插件会自动选择可用端口
"""
            return MessageChain([Plain(text)])
        
        except Exception as e:
            logger.error(f"获取 WebUI 信息失败：{e}")
            return MessageChain([Plain(f"❌ 获取失败：{e}")])