"""
基础组件 - 异常定义
"""


class MemoryError(Exception):
    """记忆操作基础异常"""
    pass


class MemoryNotFoundError(MemoryError):
    """记忆未找到"""
    def __init__(self, memory_id: str, memory_type: str = "unknown"):
        self.memory_id = memory_id
        self.memory_type = memory_type
        super().__init__(f"记忆未找到：ID={memory_id}, 类型={memory_type}")


class MemoryStoreError(MemoryError):
    """记忆存储错误"""
    pass


class MemoryRetrievalError(MemoryError):
    """记忆检索错误"""
    pass


class EmbeddingError(MemoryError):
    """嵌入向量生成错误"""
    pass


class SummarizationError(MemoryError):
    """记忆总结错误"""
    pass


class ConfigurationError(MemoryError):
    """配置错误"""
    pass


class WebUIError(MemoryError):
    """WebUI 错误"""
    pass


class DatabaseError(MemoryError):
    """数据库操作错误"""
    pass


class InitializationError(MemoryError):
    """初始化错误"""
    def __init__(self, component: str, message: str):
        self.component = component
        super().__init__(f"{component} 初始化失败：{message}")
