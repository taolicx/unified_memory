"""
存储层 - SQLite 数据库操作
"""
import asyncio
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

from ..base import (
    DatabaseError,
    TABLE_SHORT_TERM_MEMORIES,
    TABLE_LONG_TERM_MEMORIES,
    TABLE_CONVERSATIONS,
    MEMORY_STATUS_ACTIVE,
    MEMORY_STATUS_ARCHIVED
)

logger = logging.getLogger("astrbot_plugin_unified_memory")


class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._init_database()

    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建短期记忆表
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_SHORT_TERM_MEMORIES} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        persona_id TEXT,
                        content TEXT NOT NULL,
                        message_count INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT '{MEMORY_STATUS_ACTIVE}'
                    )
                """)
                
                # 创建长期记忆表
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_LONG_TERM_MEMORIES} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        persona_id TEXT,
                        content TEXT NOT NULL,
                        canonical_summary TEXT,
                        persona_summary TEXT,
                        embedding BLOB,
                        importance REAL DEFAULT 0.5,
                        access_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed_at TIMESTAMP,
                        status TEXT DEFAULT '{MEMORY_STATUS_ACTIVE}'
                    )
                """)
                
                # 创建会话表
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_CONVERSATIONS} (
                        id TEXT PRIMARY KEY,
                        persona_id TEXT,
                        user_id TEXT,
                        platform TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT '{MEMORY_STATUS_ACTIVE}'
                    )
                """)
                
                # 创建索引
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_short_term_session 
                    ON {TABLE_SHORT_TERM_MEMORIES}(session_id, status)
                """)
                
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_long_term_session 
                    ON {TABLE_LONG_TERM_MEMORIES}(session_id, status)
                """)
                
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_long_term_status 
                    ON {TABLE_LONG_TERM_MEMORIES}(status, importance)
                """)
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except sqlite3.Error as e:
            raise DatabaseError(f"数据库初始化失败：{e}")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    async def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """异步执行 SQL 查询"""
        async with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """异步查询多条记录"""
        async with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """异步查询单条记录"""
        async with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None

    # 短期记忆操作
    async def add_short_term_memory(
        self,
        session_id: str,
        content: str,
        persona_id: Optional[str] = None
    ) -> int:
        """添加短期记忆"""
        cursor = await self.execute(
            f"""
            INSERT INTO {TABLE_SHORT_TERM_MEMORIES} 
            (session_id, persona_id, content) 
            VALUES (?, ?, ?)
            """,
            (session_id, persona_id, content)
        )
        return cursor.lastrowid

    async def get_short_term_memories(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取短期记忆"""
        return await self.fetch_all(
            f"""
            SELECT * FROM {TABLE_SHORT_TERM_MEMORIES}
            WHERE session_id = ? AND status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, MEMORY_STATUS_ACTIVE, limit)
        )

    async def delete_short_term_memory(self, memory_id: int) -> bool:
        """删除短期记忆"""
        await self.execute(
            f"""
            UPDATE {TABLE_SHORT_TERM_MEMORIES}
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (MEMORY_STATUS_ARCHIVED, memory_id)
        )
        return True

    # 长期记忆操作
    async def add_long_term_memory(
        self,
        session_id: str,
        content: str,
        canonical_summary: Optional[str] = None,
        persona_summary: Optional[str] = None,
        persona_id: Optional[str] = None,
        importance: float = 0.5
    ) -> int:
        """添加长期记忆"""
        cursor = await self.execute(
            f"""
            INSERT INTO {TABLE_LONG_TERM_MEMORIES} 
            (session_id, persona_id, content, canonical_summary, 
             persona_summary, importance) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, persona_id, content, canonical_summary, 
             persona_summary, importance)
        )
        return cursor.lastrowid

    async def update_long_term_memory(
        self,
        memory_id: int,
        content: Optional[str] = None,
        canonical_summary: Optional[str] = None,
        persona_summary: Optional[str] = None,
        importance: Optional[float] = None
    ) -> bool:
        """更新长期记忆"""
        updates = []
        params = []
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if canonical_summary is not None:
            updates.append("canonical_summary = ?")
            params.append(canonical_summary)
        if persona_summary is not None:
            updates.append("persona_summary = ?")
            params.append(persona_summary)
        if importance is not None:
            updates.append("importance = ?")
            params.append(importance)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(memory_id)
            
            await self.execute(
                f"""
                UPDATE {TABLE_LONG_TERM_MEMORIES}
                SET {', '.join(updates)}
                WHERE id = ?
                """,
                tuple(params)
            )
        return True

    async def get_long_term_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """获取单条长期记忆"""
        return await self.fetch_one(
            f"""
            SELECT * FROM {TABLE_LONG_TERM_MEMORIES}
            WHERE id = ?
            """,
            (memory_id,)
        )

    async def get_long_term_memories(
        self,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取长期记忆列表"""
        conditions = ["status = ?"]
        params = [MEMORY_STATUS_ACTIVE]
        
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if persona_id:
            conditions.append("persona_id = ?")
            params.append(persona_id)
        
        query = f"""
        SELECT * FROM {TABLE_LONG_TERM_MEMORIES}
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ?
        """
        params.append(limit)
        
        return await self.fetch_all(query, tuple(params))

    async def search_long_term_memories(
        self,
        keyword: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索长期记忆"""
        return await self.fetch_all(
            f"""
            SELECT * FROM {TABLE_LONG_TERM_MEMORIES}
            WHERE status = ? 
            AND (content LIKE ? OR canonical_summary LIKE ? OR persona_summary LIKE ?)
            ORDER BY importance DESC, created_at DESC
            LIMIT ?
            """,
            (MEMORY_STATUS_ACTIVE, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit)
        )

    async def delete_long_term_memory(self, memory_id: int) -> bool:
        """删除长期记忆"""
        await self.execute(
            f"""
            UPDATE {TABLE_LONG_TERM_MEMORIES}
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (MEMORY_STATUS_ARCHIVED, memory_id)
        )
        return True

    async def update_memory_access_count(self, memory_id: int) -> bool:
        """更新记忆访问计数"""
        await self.execute(
            f"""
            UPDATE {TABLE_LONG_TERM_MEMORIES}
            SET access_count = access_count + 1, 
                last_accessed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory_id,)
        )
        return True

    async def get_old_memories(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取指定天数前的旧记忆"""
        return await self.fetch_all(
            f"""
            SELECT * FROM {TABLE_LONG_TERM_MEMORIES}
            WHERE status = ? 
            AND created_at < datetime('now', ?)
            ORDER BY importance ASC, created_at ASC
            LIMIT ?
            """,
            (MEMORY_STATUS_ACTIVE, f'-{days} days', limit)
        )

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        short_term_count = await self.fetch_one(
            f"""
            SELECT COUNT(*) as count FROM {TABLE_SHORT_TERM_MEMORIES}
            WHERE status = ?
            """,
            (MEMORY_STATUS_ACTIVE,)
        )
        
        long_term_count = await self.fetch_one(
            f"""
            SELECT COUNT(*) as count FROM {TABLE_LONG_TERM_MEMORIES}
            WHERE status = ?
            """,
            (MEMORY_STATUS_ACTIVE,)
        )
        
        session_count = await self.fetch_one(
            f"""
            SELECT COUNT(DISTINCT session_id) as count 
            FROM {TABLE_LONG_TERM_MEMORIES}
            WHERE status = ?
            """,
            (MEMORY_STATUS_ACTIVE,)
        )
        
        return {
            "short_term_count": short_term_count["count"] if short_term_count else 0,
            "long_term_count": long_term_count["count"] if long_term_count else 0,
            "session_count": session_count["count"] if session_count else 0
        }

    async def close(self):
        """关闭数据库连接"""
        logger.info("数据库连接已关闭")
