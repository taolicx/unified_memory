"""
AstrBot Plugin Unified Memory - 统一记忆插件
结合长期记忆和短期记忆，支持 WebUI 管理
"""
import asyncio
import logging
from typing import Optional
from astrbot.api import AstrBotConfig
from astrbot.api.event import filter
from astrbot.api.plugin import Plugin, ASTRBOT_VERSION

from .core.managers.memory_engine import MemoryEngine
from .core.managers.conversation_manager import ConversationManager
from .core.event_handler import EventHandler
from .core.command_handler import CommandHandler
from .core.base import api_adapter
from .webui.app import WebUIApp

logger = logging.getLogger("astrbot_plugin_unified_memory")


class UnifiedMemoryPlugin(Plugin):
    """统一记忆插件主类"""

    def __init__(self, config: AstrBotConfig):
        super().__init__()
        self.config = config
        self.memory_engine: Optional[MemoryEngine] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.event_handler: Optional[EventHandler] = None
        self.command_handler: Optional[CommandHandler] = None
        self.webui_app: Optional[WebUIApp] = None
        self._initialized = False
        
        # 检测 AstrBot 版本
        api_adapter.detect_version()

    async def initialize(self):
        """插件初始化"""
        logger.info("正在初始化统一记忆插件...")
        
        try:
            # 验证配置
            from .core.base import ConfigManager
            config_manager = ConfigManager(self.config)
            config_manager.validate()
            
            # 初始化记忆引擎
            self.memory_engine = MemoryEngine(self.config)
            await self.memory_engine.initialize()
            
            # 初始化会话管理器
            self.conversation_manager = ConversationManager(self.memory_engine)
            
            # 初始化事件处理器
            self.event_handler = EventHandler(
                self.memory_engine,
                self.conversation_manager,
                config_manager
            )
            
            # 初始化命令处理器
            self.command_handler = CommandHandler(
                self.memory_engine,
                self.conversation_manager,
                config_manager
            )
            
            # 注册事件监听（使用兼容方式）
            self.event_handler.register_events(self)
            
            # 注册命令（使用兼容方式）
            self.command_handler.register_commands(self)
            
            # 启动 WebUI
            if self.config.get("webui_settings", {}).get("enabled", True):
                self.webui_app = WebUIApp(
                    self.memory_engine,
                    self.conversation_manager,
                    config_manager
                )
                await self.webui_app.start()
                logger.info(f"WebUI 已启动：http://{self.config.get('webui_settings', {}).get('host', '127.0.0.1')}:{self.config.get('webui_settings', {}).get('port', 8080)}")
            
            self._initialized = True
            logger.info("统一记忆插件初始化完成")
            
        except Exception as e:
            logger.error(f"插件初始化失败：{e}", exc_info=True)
            raise

    async def on_enable(self):
        """插件启用时调用"""
        if not self._initialized:
            await self.initialize()

    async def on_disable(self):
        """插件禁用时调用"""
        logger.info("正在关闭统一记忆插件...")
        
        if self.webui_app:
            await self.webui_app.stop()
        
        if self.memory_engine:
            await self.memory_engine.close()
        
        logger.info("统一记忆插件已关闭")

    async def on_unload(self):
        """插件卸载时调用"""
        await self.on_disable()


# 插件导出
def create_plugin(config: AstrBotConfig) -> UnifiedMemoryPlugin:
    return UnifiedMemoryPlugin(config)
