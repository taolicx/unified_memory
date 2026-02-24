"""
基础组件 - 配置管理
"""
import logging
from typing import Any, Dict, Optional
from astrbot.api import AstrBotConfig
from .exceptions import ConfigurationError

logger = logging.getLogger("astrbot_plugin_unified_memory")


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: AstrBotConfig):
        self._config = config
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        # 支持嵌套键访问，如 "memory_settings.short_term.max_messages"
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, default)
                else:
                    value = getattr(value, k, default) if hasattr(value, k) else default
            return value if value is not None else default
        except (KeyError, AttributeError, TypeError):
            return default

    def get_required(self, key: str) -> Any:
        """获取必需配置值，如果不存在则抛出异常"""
        value = self.get(key)
        if value is None:
            raise ConfigurationError(f"必需配置项缺失：{key}")
        return value

    def get_embedding_provider_id(self) -> Optional[str]:
        """获取嵌入模型 provider ID"""
        return self.get("embedding_provider_id") or None

    def get_llm_provider_id(self) -> Optional[str]:
        """获取 LLM provider ID"""
        return self.get("llm_provider_id") or None

    def get_short_term_config(self) -> Dict[str, Any]:
        """获取短期记忆配置"""
        return self.get("memory_settings.short_term", {
            "max_messages": 50,
            "summary_threshold": 10,
            "enabled": True
        })

    def get_long_term_config(self) -> Dict[str, Any]:
        """获取长期记忆配置"""
        return self.get("memory_settings.long_term", {
            "top_k": 5,
            "auto_summary": True,
            "forgetting_enabled": True,
            "forgetting_threshold_days": 30
        })

    def get_webui_config(self) -> Dict[str, Any]:
        """获取 WebUI 配置"""
        return self.get("webui_settings", {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 8080,
            "access_password": ""
        })

    def get_retrieval_config(self) -> Dict[str, Any]:
        """获取检索配置"""
        return self.get("retrieval_settings", {
            "use_hybrid": True,
            "bm25_weight": 0.5,
            "vector_weight": 0.5
        })

    def validate(self) -> bool:
        """验证配置有效性"""
        # 检查必需配置
        webui_config = self.get_webui_config()
        if not isinstance(webui_config.get("port"), int):
            raise ConfigurationError("WebUI 端口必须是整数")
        
        if not (0 < webui_config.get("port", 0) < 65536):
            raise ConfigurationError("WebUI 端口必须在 1-65535 范围内")

        # 检查记忆配置
        short_term = self.get_short_term_config()
        if short_term.get("max_messages", 0) <= 0:
            raise ConfigurationError("短期记忆最大消息数必须大于 0")

        long_term = self.get_long_term_config()
        if long_term.get("top_k", 0) <= 0:
            raise ConfigurationError("长期记忆检索数量必须大于 0")

        return True

    def __repr__(self) -> str:
        return f"ConfigManager(config={self._config})"
