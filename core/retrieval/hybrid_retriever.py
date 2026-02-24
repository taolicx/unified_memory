"""
检索层 - 混合检索器（BM25 + 向量检索）
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from ..base import ConfigManager, MemoryRetrievalError

logger = logging.getLogger("astrbot_plugin_unified_memory")


class HybridRetriever:
    """混合检索器 - 结合 BM25 和向量检索"""

    def __init__(
        self,
        bm25_retriever,
        faiss_index,
        config_manager: ConfigManager
    ):
        self.bm25_retriever = bm25_retriever
        self.faiss_index = faiss_index
        self.config = config_manager
        self._initialized = False

    async def initialize(self):
        """初始化混合检索器"""
        await self.bm25_retriever.initialize()
        self._initialized = True
        logger.info("混合检索器已初始化")

    def _rrf_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        使用 RRF (Reciprocal Rank Fusion) 融合两个检索结果
        
        RRF 公式：score = sum(1 / (k + rank))
        """
        scores: Dict[int, float] = defaultdict(float)
        
        # BM25 结果打分
        for rank, (memory_id, score) in enumerate(bm25_results):
            scores[memory_id] += 1.0 / (k + rank + 1)
        
        # 向量检索结果打分
        for rank, (memory_id, score) in enumerate(vector_results):
            scores[memory_id] += 1.0 / (k + rank + 1)
        
        # 排序
        sorted_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_results

    def _weighted_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        使用加权融合两个检索结果
        """
        scores: Dict[int, float] = defaultdict(float)
        
        # 归一化 BM25 分数
        if bm25_results:
            max_bm25 = max(s for _, s in bm25_results)
            if max_bm25 > 0:
                for memory_id, score in bm25_results:
                    scores[memory_id] += bm25_weight * (score / max_bm25)
        
        # 归一化向量检索分数
        if vector_results:
            max_vector = max(s for _, s in vector_results) if vector_results else 0
            if max_vector > 0:
                for memory_id, score in vector_results:
                    scores[memory_id] += vector_weight * (score / max_vector)
        
        # 排序
        sorted_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_results

    async def search(
        self,
        query: str,
        query_vector: Optional[Any] = None,
        k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            query_vector: 查询向量（numpy 数组）
            k: 返回结果数量
        
        Returns:
            List[Tuple[memory_id, score]]
        """
        if not self._initialized:
            raise MemoryRetrievalError("混合检索器未初始化")
        
        retrieval_config = self.config.get_retrieval_config()
        use_hybrid = retrieval_config.get("use_hybrid", True)
        
        if not use_hybrid:
            # 只使用向量检索
            if query_vector is not None:
                return await self.faiss_index.search(query_vector, k)
            return []
        
        # 并行执行两种检索
        bm25_task = self.bm25_retriever.search(query, k * 2)
        
        vector_results = []
        if query_vector is not None:
            vector_task = self.faiss_index.search(query_vector, k * 2)
            bm25_results, vector_results = await (bm25_task, vector_task)
        else:
            bm25_results = await bm25_task
        
        # 融合结果
        if retrieval_config.get("use_rrf", True):
            fused_results = self._rrf_fusion(bm25_results, vector_results)
        else:
            bm25_weight = retrieval_config.get("bm25_weight", 0.5)
            vector_weight = retrieval_config.get("vector_weight", 0.5)
            fused_results = self._weighted_fusion(
                bm25_results, 
                vector_results,
                bm25_weight,
                vector_weight
            )
        
        # 返回 top-k
        return fused_results[:k]

    async def add_memory(
        self,
        memory_id: int,
        content: str,
        vector: Optional[Any] = None
    ):
        """添加记忆到检索索引"""
        tasks = [
            self.bm25_retriever.add_documents([memory_id], [content])
        ]
        
        if vector is not None:
            import numpy as np
            tasks.append(
                self.faiss_index.add_vectors(
                    [memory_id], 
                    np.array(vector).reshape(1, -1)
                )
            )
        
        await tasks

    async def remove_memory(self, memory_id: int):
        """从检索索引中移除记忆"""
        await self.bm25_retriever.remove_documents([memory_id])
        await self.faiss_index.remove_vectors([memory_id])

    async def rebuild_index(
        self,
        memory_ids: List[int],
        contents: List[str],
        vectors: Optional[List[Any]] = None
    ):
        """重建检索索引"""
        await self.bm25_retriever.rebuild_index(memory_ids, contents)
        
        if vectors:
            import numpy as np
            await self.faiss_index.rebuild_index(
                memory_ids,
                np.array(vectors)
            )

    async def get_stats(self) -> Dict[str, int]:
        """获取检索器统计信息"""
        return {
            "bm25_count": await self.bm25_retriever.get_document_count(),
            "vector_count": await self.faiss_index.get_vector_count()
        }

    async def close(self):
        """关闭检索器"""
        await self.bm25_retriever.close()
        await self.faiss_index.close()
        logger.info("混合检索器已关闭")
