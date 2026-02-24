"""
AstrBot API 适配器 - 确保与不同版本 AstrBot 兼容
"""
import logging
from typing import Optional, Any, Callable
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Plain

logger = logging.getLogger("astrbot_plugin_unified_memory")


class AstrBotAPIAdapter:
    """AstrBot API 适配器
    
    用于兼容不同版本的 AstrBot，自动检测 API 可用性
    """
    
    def __init__(self):
        self._astrbot_version: Optional[str] = None
        self._supports_async: bool = True
        self._supports_context_injection: bool = True
        
    def detect_version(self) -> str:
        """检测 AstrBot 版本"""
        try:
            from astrbot import __version__
            self._astrbot_version = __version__
            logger.info(f"检测到 AstrBot 版本：{__version__}")
            return __version__
        except (ImportError, AttributeError):
            logger.warning("无法检测 AstrBot 版本，使用兼容模式")
            return "unknown"
    
    def register_event_handler(self, plugin, event_type: str, handler: Callable):
        """注册事件处理器 - 兼容不同版本
        
        Args:
            plugin: 插件实例
            event_type: 事件类型，如 "on_message"
            handler: 处理函数
        """
        try:
            # 尝试使用新 API
            if hasattr(plugin, 'register_event_handler'):
                plugin.register_event_handler(event_type, handler)
                logger.debug(f"已注册事件处理器：{event_type}")
            else:
                logger.warning("插件不支持 register_event_handler 方法")
        except Exception as e:
            logger.error(f"注册事件处理器失败：{e}")
    
    def register_command(self, plugin, command_names: list, handler: Callable):
        """注册命令 - 兼容不同版本
        
        Args:
            plugin: 插件实例
            command_names: 命令名称列表，如 ["umem", "umem_help"]
            handler: 处理函数
        """
        try:
            if hasattr(plugin, 'register_command'):
                plugin.register_command(command_names, handler)
                logger.debug(f"已注册命令：{command_names}")
            else:
                logger.warning("插件不支持 register_command 方法")
        except Exception as e:
            logger.error(f"注册命令失败：{e}")
    
    def get_session_id(self, event: AstrMessageEvent) -> str:
        """获取会话 ID - 兼容不同版本"""
        try:
            return event.get_session_id()
        except AttributeError:
            # 备用方案
            try:
                return f"{event.platform}_{event.user_id}"
            except Exception:
                return "unknown_session"
    
    def get_platform_name(self, event: AstrMessageEvent) -> str:
        """获取平台名称 - 兼容不同版本"""
        try:
            return event.get_platform_name()
        except AttributeError:
            try:
                return event.platform
            except Exception:
                return "unknown"
    
    def get_message_text(self, event: AstrMessageEvent) -> str:
        """获取消息文本 - 兼容不同版本"""
        try:
            message_text = ""
            for comp in event.message_obj.message:
                if isinstance(comp, Plain):
                    message_text += comp.text
            return message_text
        except Exception as e:
            logger.error(f"获取消息文本失败：{e}")
            return ""
    
    def set_extra(self, event: AstrMessageEvent, key: str, value: Any):
        """设置额外数据 - 兼容不同版本"""
        try:
            if hasattr(event, 'set_extra'):
                event.set_extra(key, value)
            elif hasattr(event, 'context'):
                event.context[key] = value
        except Exception as e:
            logger.debug(f"设置额外数据失败（非致命）：{e}")
    
    def create_message_chain(self, text: str) -> MessageChain:
        """创建消息链 - 兼容不同版本"""
        return MessageChain([Plain(text)])


# 全局适配器实例
api_adapter = AstrBotAPIAdapter()
