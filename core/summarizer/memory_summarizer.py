"""
记忆总结器 - 使用 LLM 生成记忆摘要
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..base import SummarizationError, ConfigManager

logger = logging.getLogger("astrbot_plugin_unified_memory")


class MemorySummarizer:
    """记忆总结器"""

    def __init__(
        self,
        llm_provider_id: Optional[str],
        config_manager: ConfigManager
    ):
        self.llm_provider_id = llm_provider_id
        self.config = config_manager
        self._llm_provider = None
        self._initialized = False

    async def initialize(self, llm_provider: Any):
        """初始化总结器"""
        self._llm_provider = llm_provider
        self._initialized = True
        logger.info("记忆总结器已初始化")

    def _build_summary_prompt(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> str:
        """构建总结提示词"""
        # 格式化对话历史
        conversation = "\n".join([
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in messages
        ])
        
        prompt = f"""请总结以下对话内容，提取关键信息和事实。

对话历史：
{conversation}

请按照以下格式输出总结：
1. 主要话题和讨论内容
2. 关键事实和重要信息
3. 用户的偏好、习惯或特点
4. 需要记住的其他信息

要求：
- 简洁明了，突出重点
- 使用第三人称
- 避免冗余信息
- 保持客观准确
"""
        
        if context:
            prompt = f"当前背景：{context}\n\n{prompt}"
        
        return prompt

    def _build_persona_prompt(
        self,
        messages: List[Dict[str, str]],
        canonical_summary: str
    ) -> str:
        """构建人格化总结提示词"""
        prompt = f"""基于以下事实总结，生成一段自然流畅的人格化描述，用于对话注入。

事实总结：
{canonical_summary}

要求：
- 使用第一人称（"我记得..."）
- 自然流畅，像真人的回忆
- 适合在对话中自然提及
- 保持简洁，100 字以内
"""
        return prompt

    async def summarize(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        总结对话内容
        
        Args:
            messages: 对话消息列表
            context: 额外上下文
        
        Returns:
            (canonical_summary, persona_summary)
        """
        if not self._initialized:
            raise SummarizationError("总结器未初始化")
        
        if not self._llm_provider:
            raise SummarizationError("LLM Provider 未配置")
        
        try:
            # 生成事实总结
            prompt = self._build_summary_prompt(messages, context)
            canonical_summary = await self._call_llm(prompt)
            
            # 生成人格化总结
            persona_prompt = self._build_persona_prompt(messages, canonical_summary)
            persona_summary = await self._call_llm(persona_prompt)
            
            logger.debug(f"总结完成：canonical={len(canonical_summary)}字，persona={len(persona_summary)}字")
            
            return canonical_summary, persona_summary
            
        except Exception as e:
            logger.error(f"总结失败：{e}")
            raise SummarizationError(f"总结失败：{e}")

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成响应"""
        try:
            # 使用 AstrBot 的 Provider 接口
            response = await self._llm_provider.text_chat(
                prompt=prompt,
                session_id="memory_summarizer"
            )
            return response.completion_text.strip()
        except Exception as e:
            logger.error(f"LLM 调用失败：{e}")
            raise SummarizationError(f"LLM 调用失败：{e}")

    async def evaluate_importance(
        self,
        content: str,
        context: Optional[str] = None
    ) -> float:
        """
        评估记忆重要性（0-1 之间）
        
        考虑因素：
        - 信息的新颖性
        - 与用户的相关性
        - 情感强度
        - 实用性
        """
        if not self._llm_provider:
            # 默认重要性
            return 0.5
        
        prompt = f"""请评估以下记忆内容的重要性，返回 0-1 之间的分数。

记忆内容：
{content}

评分标准：
- 0.0-0.2: 非常不重要（日常寒暄、无关信息）
- 0.2-0.4: 不太重要（一般信息、临时话题）
- 0.4-0.6: 中等重要（有用信息、个人偏好）
- 0.6-0.8: 重要（关键事实、重要偏好）
- 0.8-1.0: 非常重要（核心信息、关键特征）

只需返回一个数字（0-1 之间），不要有其他内容。
"""
        
        try:
            response = await self._call_llm(prompt)
            # 解析数字
            import re
            match = re.search(r'[\d.]+', response)
            if match:
                score = float(match.group())
                return max(0.0, min(1.0, score))
        except Exception as e:
            logger.warning(f"重要性评估失败：{e}，使用默认值")
        
        return 0.5

    async def close(self):
        """关闭总结器"""
        self._initialized = False
        logger.debug("记忆总结器已关闭")