"""
记忆引擎 - 核心记忆管理
"""
import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from astrbot.api.provider import Provider

from ..base import (
    ConfigManager,
    MemoryNotFoundError,
    MemoryStoreError,
    EmbeddingError,
    InitializationError,
    MEMORY_TYPE_SHORT_TERM,
    MEMORY_TYPE_LONG_TERM,
    MEMORY_STATUS_ACTIVE
)
from ..storage import Database, FaissIndex
from ..retrieval import BM25Retriever, HybridRetriever
from ..summarizer import MemorySummarizer

logger = logging.getLogger("astrbot_plugin_unified_memory")


class MemoryEngine:
    """统一记忆引擎 - 管理短期和长期记忆"""

    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.db: Optional[Database] = None
        self.faiss_index: Optional[FaissIndex] = None
        self.retriever: Optional[HybridRetriever] = None
        self.summarizer: Optional[MemorySummarizer] = None
        self._embedding_provider: Optional[Provider] = None
        self._llm_provider: Optional[Provider] = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(
        self,
        embedding_provider: Optional[Provider] = None,
        llm_provider: Optional[Provider] = None
    ):
        """初始化记忆引擎"""
        async with self._lock:
            if self._initialized:
                return
            
            logger.info("正在初始化记忆引擎...")
            
            try:
                # 获取 Provider
                self._embedding_provider = embedding_provider
                self._llm_provider = llm_provider
                
                # 初始化数据库
                db_path = "data/plugins/astrbot_plugin_unified_memory/memory.db"
                self.db = Database(db_path)
                logger.info("数据库已初始化")
                
                # 初始化 Faiss 索引
                faiss_path = "data/plugins/astrbot_plugin_unified_memory/faiss_index"
                self.faiss_index = FaissIndex(faiss_path)
                
                # 获取向量维度
                dimension = await self._get_embedding_dimension()
                await self.faiss_index.initialize(dimension)
                logger.info(f"Faiss 索引已初始化，维度={dimension}")
                
                # 初始化 BM25 检索器
                bm25_retriever = BM25Retriever()
                
                # 初始化混合检索器
                self.retriever = HybridRetriever(
                    bm25_retriever,
                    self.faiss_index,
                    self.config
                )
                await self.retriever.initialize()
                logger.info("检索器已初始化")
                
                # 初始化总结器
                self.summarizer = MemorySummarizer(
                    self.config.get_llm_provider_id(),
                    self.config
                )
                if llm_provider:
                    await self.summarizer.initialize(llm_provider)
                    logger.info("总结器已初始化")
                
                # 加载现有记忆到检索索引
                await self._load_memories_to_index()
                
                self._initialized = True
                logger.info("记忆引擎初始化完成")
                
            except Exception as e:
                logger.error(f"记忆引擎初始化失败：{e}", exc_info=True)
                raise InitializationError("MemoryEngine", str(e))

    async def _get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        if not self._embedding_provider:
            logger.warning("Embedding Provider 未配置，使用默认维度 768")
            return 768
        
        try:
            # 通过一次嵌入获取维度
            test_text = "test"
            embedding = await self._get_embedding(test_text)
            return len(embedding)
        except Exception as e:
            logger.warning(f"获取嵌入维度失败：{e}，使用默认维度 768")
            return 768

    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        if not self._embedding_provider:
            raise EmbeddingError("Embedding Provider 未配置")
        
        try:
            # 调用 AstrBot 的 Embedding Provider
            result = await self._embedding_provider.get_embedding(text)
            return result
        except Exception as e:
            logger.error(f"获取嵌入向量失败：{e}")
            raise EmbeddingError(f"获取嵌入向量失败：{e}")

    async def _load_memories_to_index(self):
        """加载现有记忆到检索索引"""
        try:
            memories = await self.db.get_long_term_memories(limit=1000)
            
            if memories:
                memory_ids = [m["id"] for m in memories]
                contents = [m["content"] for m in memories]
                
                # 重建 BM25 索引
                await self.retriever.bm25_retriever.rebuild_index(memory_ids, contents)
                
                # 重建向量索引
                vectors = []
                for m in memories:
                    if m.get("embedding"):
                        import pickle
                        vector = pickle.loads(m["embedding"])
                        vectors.append(vector)
                
                if vectors:
                    await self.faiss_index.rebuild_index(
                        memory_ids,
                        np.array(vectors)
                    )
                
                logger.info(f"已加载 {len(memories)} 条记忆到检索索引")
        
        except Exception as e:
            logger.warning(f"加载记忆到索引失败：{e}")

    # ========== 短期记忆操作 ==========
    
    async def add_short_term_memory(
        self,
        session_id: str,
        content: str,
        persona_id: Optional[str] = None
    ) -> int:
        """添加短期记忆"""
        memory_id = await self.db.add_short_term_memory(
            session_id, content, persona_id
        )
        logger.debug(f"添加短期记忆：id={memory_id}, session={session_id}")
        return memory_id

    async def get_short_term_memories(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取短期记忆"""
        return await self.db.get_short_term_memories(session_id, limit)

    async def delete_short_term_memory(self, memory_id: int) -> bool:
        """删除短期记忆"""
        return await self.db.delete_short_term_memory(memory_id)

    async def clear_short_term_memories(self, session_id: str) -> int:
        """清除会话的所有短期记忆"""
        memories = await self.get_short_term_memories(session_id, limit=1000)
        for m in memories:
            await self.delete_short_term_memory(m["id"])
        return len(memories)

    # ========== 长期记忆操作 ==========
    
    async def add_long_term_memory(
        self,
        session_id: str,
        content: str,
        canonical_summary: Optional[str] = None,
        persona_summary: Optional[str] = None,
        persona_id: Optional[str] = None,
        importance: Optional[float] = None,
        vector: Optional[List[float]] = None
    ) -> int:
        """添加长期记忆"""
        # 如果没有提供向量，生成嵌入
        if vector is None and self._embedding_provider:
            vector = await self._get_embedding(content)
        
        # 序列化向量
        import pickle
        embedding_blob = pickle.dumps(vector) if vector else None
        
        # 如果未提供重要性，评估重要性
        if importance is None and self.summarizer:
            importance = await self.summarizer.evaluate_importance(content)
        
        # 添加到数据库
        memory_id = await self.db.add_long_term_memory(
            session_id=session_id,
            content=content,
            canonical_summary=canonical_summary,
            persona_summary=persona_summary,
            persona_id=persona_id,
            importance=importance or 0.5
        )
        
        # 添加到检索索引
        if self.retriever and vector:
            await self.retriever.add_memory(memory_id, content, vector)
        
        logger.debug(f"添加长期记忆：id={memory_id}, session={session_id}")
        return memory_id

    async def get_long_term_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """获取单条长期记忆"""
        memory = await self.db.get_long_term_memory(memory_id)
        if memory:
            # 更新访问计数
            await self.db.update_memory_access_count(memory_id)
            # 反序列化向量
            if memory.get("embedding"):
                import pickle
                memory["vector"] = pickle.loads(memory["embedding"])
        return memory

    async def get_long_term_memories(
        self,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取长期记忆列表"""
        return await self.db.get_long_term_memories(
            session_id, persona_id, limit
        )

    async def update_long_term_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        canonical_summary: Optional[str] = None,
        persona_summary: Optional[str] = None,
        importance: Optional[float] = None
    ) -> bool:
        """更新长期记忆"""
        # 获取原记忆
        memory = await self.get_long_term_memory(memory_id)
        if not memory:
            raise MemoryNotFoundError(str(memory_id), MEMORY_TYPE_LONG_TERM)
        
        # 更新数据库
        await self.db.update_long_term_memory(
            memory_id, content, canonical_summary, persona_summary, importance
        )
        
        # 如果内容改变，更新检索索引
        if content and content != memory["content"]:
            await self.retriever.remove_memory(memory_id)
            vector = memory.get("vector")
            if vector is None and self._embedding_provider:
                vector = await self._get_embedding(content)
            if vector:
                await self.retriever.add_memory(memory_id, content, vector)
        
        return True

    async def delete_long_term_memory(self, memory_id: int) -> bool:
        """删除长期记忆"""
        # 从检索索引移除
        await self.retriever.remove_memory(memory_id)
        
        # 从数据库删除
        return await self.db.delete_long_term_memory(memory_id)

    async def search_memories(
        self,
        query: str,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        # 获取查询向量
        query_vector = None
        if self._embedding_provider:
            query_vector = await self._get_embedding(query)
        
        # 执行检索
        results = await self.retriever.search(query, query_vector, k)
        
        # 获取完整记忆信息
        memories = []
        for memory_id, score in results:
            memory = await self.get_long_term_memory(memory_id)
            if memory:
                memory["score"] = score
                memories.append(memory)
        
        return memories

    async def summarize_and_store(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        persona_id: Optional[str] = None
    ) -> int:
        """总结对话并存储为长期记忆"""
        if not self.summarizer:
            raise MemoryStoreError("总结器未初始化")
        
        # 生成总结
        canonical_summary, persona_summary = await self.summarizer.summarize(
            messages,
            context=f"session_id={session_id}"
        )
        
        # 合并内容
        content = f"{canonical_summary}\n\n{persona_summary}"
        
        # 存储为长期记忆
        memory_id = await self.add_long_term_memory(
            session_id=session_id,
            content=content,
            canonical_summary=canonical_summary,
            persona_summary=persona_summary,
            persona_id=persona_id
        )
        
        logger.info(f"对话已总结并存储：memory_id={memory_id}")
        return memory_id

    # ========== 统计和管理 ==========
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        db_stats = await self.db.get_stats()
        retrieval_stats = await self.retriever.get_stats() if self.retriever else {}
        
        return {
            **db_stats,
            "retrieval": retrieval_stats,
            "initialized": self._initialized
        }

    async def cleanup_old_memories(
        self,
        days: int = 30,
        dry_run: bool = True
    ) -> List[int]:
        """清理旧记忆"""
        old_memories = await self.db.get_old_memories(days)
        
        # 按重要性排序，删除重要性低的
        to_delete = []
        for m in sorted(old_memories, key=lambda x: x.get("importance", 0.5)):
            to_delete.append(m["id"])
        
        if not dry_run:
            for memory_id in to_delete:
                await self.delete_long_term_memory(memory_id)
        
        logger.info(f"清理旧记忆：{'将' if dry_run else '已'}删除 {len(to_delete)} 条")
        return to_delete

    async def rebuild_index(self):
        """重建检索索引"""
        memories = await self.db.get_long_term_memories(limit=1000)
        
        if memories:
            memory_ids = [m["id"] for m in memories]
            contents = [m["content"] for m in memories]
            
            # 重新生成向量
            vectors = []
            if self._embedding_provider:
                for m in memories:
                    vector = await self._get_embedding(m["content"])
                    vectors.append(vector)
                    # 更新数据库中的向量
                    import pickle
                    await self.db.execute(
                        "UPDATE long_term_memories SET embedding = ? WHERE id = ?",
                        (pickle.dumps(vector), m["id"])
                    )
            
            # 重建索引
            await self.retriever.rebuild_index(
                memory_ids,
                contents,
                vectors if vectors else None
            )
            
            logger.info(f"检索索引已重建，共 {len(memories)} 条记忆")

    async def close(self):
        """关闭记忆引擎"""
        async with self._lock:
            if self.summarizer:
                await self.summarizer.close()
            if self.retriever:
                await self.retriever.close()
            if self.faiss_index:
                await self.faiss_index.close()
            if self.db:
                await self.db.close()
            
            self._initialized = False
            logger.info("记忆引擎已关闭")