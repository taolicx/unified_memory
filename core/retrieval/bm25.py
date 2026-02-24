"""
检索层 - BM25 稀疏检索
"""
import logging
from typing import Dict, List, Tuple
from rank_bm25 import BM25Okapi

logger = logging.getLogger("astrbot_plugin_unified_memory")


class BM25Retriever:
    """BM25 文本检索器"""

    def __init__(self):
        self._bm25: Optional[BM25Okapi] = None
        self._documents: List[str] = []
        self._doc_ids: List[int] = []
        self._initialized = False

    async def initialize(self):
        """初始化 BM25 检索器"""
        self._documents = []
        self._doc_ids = []
        self._initialized = True
        logger.debug("BM25 检索器已初始化")

    def _tokenize(self, text: str) -> List[str]:
        """文本分词（简单按空格和标点分词）"""
        # 中文可以按字符分词，或者使用 jieba 等分词库
        # 这里使用简单的分词方式
        import re
        # 移除标点，按空格分词
        text = re.sub(r'[^\w\s]', ' ', text)
        # 中文按字符分词
        tokens = list(text.replace(' ', ''))
        return [t for t in tokens if t.strip()]

    async def add_documents(
        self, 
        memory_ids: List[int], 
        contents: List[str]
    ):
        """添加文档到索引"""
        for memory_id, content in zip(memory_ids, contents):
            self._doc_ids.append(memory_id)
            self._documents.append(self._tokenize(content))
        
        # 重建 BM25 索引
        if self._documents:
            self._bm25 = BM25Okapi(self._documents)
        
        logger.debug(f"BM25 已添加 {len(memory_ids)} 条文档，总计 {len(self._documents)} 条")

    async def search(
        self, 
        query: str, 
        k: int = 10
    ) -> List[Tuple[int, float]]:
        """搜索相关文档"""
        if not self._initialized or self._bm25 is None:
            return []
        
        if len(self._documents) == 0:
            return []
        
        # 分词查询
        query_tokens = self._tokenize(query)
        
        # 获取 BM25 分数
        scores = self._bm25.get_scores(query_tokens)
        
        # 获取 top-k
        k = min(k, len(scores))
        top_indices = sorted(
            range(len(scores)), 
            key=lambda i: scores[i], 
            reverse=True
        )[:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                memory_id = self._doc_ids[idx]
                results.append((memory_id, float(scores[idx])))
        
        return results

    async def remove_documents(self, memory_ids: List[int]) -> bool:
        """移除文档（需要重建索引）"""
        # 创建新的文档列表
        new_docs = []
        new_ids = []
        
        for doc_id, doc in zip(self._doc_ids, self._documents):
            if doc_id not in memory_ids:
                new_ids.append(doc_id)
                new_docs.append(doc)
        
        self._doc_ids = new_ids
        self._documents = new_docs
        
        # 重建 BM25
        if self._documents:
            self._bm25 = BM25Okapi(self._documents)
        else:
            self._bm25 = None
        
        return True

    async def rebuild_index(
        self, 
        memory_ids: List[int], 
        contents: List[str]
    ):
        """重建索引"""
        self._doc_ids = memory_ids
        self._documents = [self._tokenize(c) for c in contents]
        
        if self._documents:
            self._bm25 = BM25Okapi(self._documents)
        else:
            self._bm25 = None
        
        logger.info(f"BM25 索引已重建，文档数={len(self._documents)}")

    async def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self._documents)

    async def close(self):
        """关闭检索器"""
        self._documents = []
        self._doc_ids = []
        self._bm25 = None
        logger.debug("BM25 检索器已关闭")
