"""
存储层 - Faiss 向量索引管理
"""
import asyncio
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import faiss
except ImportError:
    faiss = None

from ..base import MemoryStoreError, EmbeddingError

logger = logging.getLogger("astrbot_plugin_unified_memory")


class FaissIndex:
    """Faiss 向量索引管理类"""

    def __init__(self, index_path: str, dimension: int = 768):
        if faiss is None:
            raise MemoryStoreError("faiss-cpu 未安装，请运行 pip install faiss-cpu")
        
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self._index: Optional[faiss.IndexFlatIP] = None
        self._id_map: Dict[int, int] = {}  # memory_id -> index_id
        self._lock = asyncio.Lock()
        self._initialized = False

    def _create_index(self):
        """创建新的向量索引"""
        # 使用内积相似度（余弦相似度需要归一化）
        self._index = faiss.IndexFlatIP(self.dimension)
        self._id_map = {}
        self._initialized = True

    def _load_index(self):
        """加载已存在的索引"""
        index_file = self.index_path / "vector_index.faiss"
        id_map_file = self.index_path / "id_map.pkl"
        
        if index_file.exists() and id_map_file.exists():
            try:
                self._index = faiss.read_index(str(index_file))
                with open(id_map_file, "rb") as f:
                    self._id_map = pickle.load(f)
                self._initialized = True
                logger.info(f"已加载 Faiss 索引，维度={self.dimension}, 向量数={self._index.ntotal}")
            except Exception as e:
                logger.warning(f"加载 Faiss 索引失败：{e}，将创建新索引")
                self._create_index()
        else:
            self._create_index()

    def _save_index(self):
        """保存索引到磁盘"""
        if not self._initialized or self._index is None:
            return
        
        index_file = self.index_path / "vector_index.faiss"
        id_map_file = self.index_path / "id_map.pkl"
        
        try:
            faiss.write_index(self._index, str(index_file))
            with open(id_map_file, "wb") as f:
                pickle.dump(self._id_map, f)
            logger.debug(f"Faiss 索引已保存，向量数={self._index.ntotal}")
        except Exception as e:
            logger.error(f"保存 Faiss 索引失败：{e}")

    async def initialize(self, dimension: Optional[int] = None):
        """初始化索引"""
        async with self._lock:
            if dimension:
                self.dimension = dimension
            self._load_index()

    async def add_vectors(
        self, 
        memory_ids: List[int], 
        vectors: np.ndarray
    ) -> List[int]:
        """添加向量到索引"""
        if not self._initialized:
            raise MemoryStoreError("Faiss 索引未初始化")
        
        async with self._lock:
            # 归一化向量（用于余弦相似度）
            if len(vectors.shape) == 1:
                vectors = vectors.reshape(1, -1)
            
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1  # 避免除零
            vectors_normalized = vectors / norms
            
            # 添加到索引
            start_id = self._index.ntotal
            self._index.add(vectors_normalized.astype(np.float32))
            
            # 更新 ID 映射
            for i, memory_id in enumerate(memory_ids):
                self._id_map[start_id + i] = memory_id
            
            # 定期保存
            self._save_index()
            
            return list(range(start_id, start_id + len(memory_ids)))

    async def search(
        self, 
        query_vector: np.ndarray, 
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """搜索最相似的向量"""
        if not self._initialized or self._index is None:
            return []
        
        if self._index.ntotal == 0:
            return []
        
        async with self._lock:
            # 归一化查询向量
            if len(query_vector.shape) == 1:
                query_vector = query_vector.reshape(1, -1)
            
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
            
            # 搜索
            k = min(k, self._index.ntotal)
            distances, indices = self._index.search(
                query_vector.astype(np.float32), 
                k
            )
            
            # 转换结果
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx in self._id_map:
                    memory_id = self._id_map[idx]
                    results.append((memory_id, float(dist)))
            
            return results

    async def remove_vectors(self, memory_ids: List[int]) -> bool:
        """从索引中移除向量（标记删除）"""
        # Faiss 不支持直接删除，需要重建索引
        # 这里采用简化的方式：记录已删除的 ID，搜索时过滤
        async with self._lock:
            to_remove = []
            for idx, mem_id in self._id_map.items():
                if mem_id in memory_ids:
                    to_remove.append(idx)
            
            for idx in to_remove:
                del self._id_map[idx]
            
            if to_remove:
                self._save_index()
            
            return True

    async def rebuild_index(self, memory_ids: List[int], vectors: np.ndarray):
        """重建索引"""
        async with self._lock:
            self._create_index()
            
            if len(vectors.shape) == 1:
                vectors = vectors.reshape(1, -1)
            
            # 归一化
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1
            vectors_normalized = vectors / norms
            
            self._index.add(vectors_normalized.astype(np.float32))
            
            for i, memory_id in enumerate(memory_ids):
                self._id_map[i] = memory_id
            
            self._save_index()
            logger.info(f"Faiss 索引已重建，向量数={self._index.ntotal}")

    async def get_vector_count(self) -> int:
        """获取索引中的向量数量"""
        if not self._initialized or self._index is None:
            return 0
        return self._index.ntotal

    async def close(self):
        """关闭并保存索引"""
        async with self._lock:
            self._save_index()
            logger.info("Faiss 索引已关闭")
