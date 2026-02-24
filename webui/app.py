"""
WebUI 应用 - 记忆管理 Web 界面
"""
import asyncio
import logging
import socket
import json
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn import Config, Server
from pathlib import Path

from ..base import ConfigManager, WEBUI_TEMPLATE
from ..managers import MemoryEngine, ConversationManager

logger = logging.getLogger("astrbot_plugin_unified_memory")


def is_port_in_use(host: str, port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            result = s.connect_ex((host, port))
            return result == 0
        except Exception:
            return False


def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        if not is_port_in_use(host, port):
            return port
    raise RuntimeError(f"无法在 {host} 上找到可用端口（尝试范围：{start_port}-{start_port + max_attempts - 1}）")


class WebUIApp:
    """WebUI 应用"""

    def __init__(
        self,
        memory_engine: MemoryEngine,
        conversation_manager: ConversationManager,
        config: ConfigManager
    ):
        self.memory_engine = memory_engine
        self.conversation_manager = conversation_manager
        self.config = config
        
        webui_config = config.get_webui_config()
        self.host = webui_config.get("host", "127.0.0.1")
        self.requested_port = webui_config.get("port", 8080)
        self.access_password = webui_config.get("access_password", "")
        self.actual_port: Optional[int] = None
        
        self.app = FastAPI(title="统一记忆管理")
        self._server: Optional[Server] = None
        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """首页"""
            content = await self._render_home()
            return self._render_template(request, content)
        
        @self.app.get("/api/stats")
        async def get_stats():
            """获取统计信息"""
            stats = await self.memory_engine.get_stats()
            return JSONResponse(stats)
        
        @self.app.get("/api/short-term")
        async def get_short_term(session_id: Optional[str] = None, limit: int = 50):
            """获取短期记忆"""
            if not session_id:
                return JSONResponse({"error": "session_id required"})
            
            memories = await self.memory_engine.get_short_term_memories(
                session_id, limit
            )
            return JSONResponse({"memories": memories})
        
        @self.app.get("/api/long-term")
        async def get_long_term(
            session_id: Optional[str] = None,
            persona_id: Optional[str] = None,
            limit: int = 100
        ):
            """获取长期记忆"""
            memories = await self.memory_engine.get_long_term_memories(
                session_id, persona_id, limit
            )
            return JSONResponse({"memories": memories})
        
        @self.app.get("/api/memory/{memory_id}")
        async def get_memory(memory_id: int, memory_type: str = "long_term"):
            """获取单条记忆"""
            if memory_type == "short_term":
                # 短期记忆需要 session_id
                return JSONResponse({"error": "Use list endpoint for short-term"})
            
            memory = await self.memory_engine.get_long_term_memory(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            
            return JSONResponse({"memory": memory})
        
        @self.app.put("/api/memory/{memory_id}")
        async def update_memory(memory_id: int, data: Dict[str, Any]):
            """更新记忆"""
            content = data.get("content")
            canonical_summary = data.get("canonical_summary")
            persona_summary = data.get("persona_summary")
            importance = data.get("importance")
            
            await self.memory_engine.update_long_term_memory(
                memory_id,
                content=content,
                canonical_summary=canonical_summary,
                persona_summary=persona_summary,
                importance=importance
            )
            
            return JSONResponse({"success": True, "message": "Memory updated"})
        
        @self.app.delete("/api/memory/{memory_id}")
        async def delete_memory(memory_id: int, memory_type: str = "long_term"):
            """删除记忆"""
            if memory_type == "short_term":
                await self.memory_engine.delete_short_term_memory(memory_id)
            else:
                await self.memory_engine.delete_long_term_memory(memory_id)
            
            return JSONResponse({"success": True, "message": "Memory deleted"})
        
        @self.app.get("/api/search")
        async def search_memories(query: str, k: int = 10):
            """搜索记忆"""
            if not query:
                return JSONResponse({"error": "query required"})
            
            memories = await self.memory_engine.search_memories(query, k)
            return JSONResponse({"memories": memories})
        
        @self.app.post("/api/memory")
        async def create_memory(data: Dict[str, Any]):
            """创建新记忆"""
            session_id = data.get("session_id")
            content = data.get("content")
            canonical_summary = data.get("canonical_summary")
            persona_summary = data.get("persona_summary")
            memory_type = data.get("type", "long_term")
            
            if not session_id or not content:
                raise HTTPException(status_code=400, detail="session_id and content required")
            
            if memory_type == "short_term":
                memory_id = await self.memory_engine.add_short_term_memory(
                    session_id, content
                )
            else:
                memory_id = await self.memory_engine.add_long_term_memory(
                    session_id, content, canonical_summary, persona_summary
                )
            
            return JSONResponse({
                "success": True,
                "memory_id": memory_id
            })
        
        @self.app.get("/api/sessions")
        async def get_sessions():
            """获取所有会话"""
            sessions = await self.conversation_manager.get_all_sessions()
            return JSONResponse({"sessions": sessions})

    def _render_template(self, request: Request, content: str) -> HTMLResponse:
        """渲染模板"""
        template = WEBUI_TEMPLATE.replace("{{ content|safe }}", content)
        return HTMLResponse(template)

    async def _render_home(self) -> str:
        """渲染首页"""
        stats = await self.memory_engine.get_stats()
        
        return f"""
        <h2>🧠 统一记忆管理</h2>
        
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="stats-card">
                    <h5><i class="bi bi-lightning text-success"></i> 短期记忆</h5>
                    <h2 class="text-success">{stats.get('short_term_count', 0)}</h2>
                    <p class="text-muted">条</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stats-card">
                    <h5><i class="bi bi-database text-primary"></i> 长期记忆</h5>
                    <h2 class="text-primary">{stats.get('long_term_count', 0)}</h2>
                    <p class="text-muted">条</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stats-card">
                    <h5><i class="bi bi-people text-info"></i> 会话数量</h5>
                    <h2 class="text-info">{stats.get('session_count', 0)}</h2>
                    <p class="text-muted">个</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-search"></i> 搜索记忆</h5>
            </div>
            <div class="card-body">
                <div class="input-group">
                    <input type="text" id="searchInput" class="form-control" placeholder="输入搜索关键词...">
                    <button class="btn btn-primary" onclick="searchMemories()">
                        <i class="bi bi-search"></i> 搜索
                    </button>
                </div>
                <div id="searchResults" class="mt-3"></div>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-header">
                <h5><i class="bi bi-list"></i> 最近记忆</h5>
            </div>
            <div class="card-body">
                <div id="recentMemories">加载中...</div>
            </div>
        </div>
        
        <script>
        async function searchMemories() {{
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            
            const response = await fetch(`/api/search?query=${{encodeURIComponent(query)}}`);
            const data = await response.json();
            
            const resultsDiv = document.getElementById('searchResults');
            if (data.memories && data.memories.length > 0) {{
                resultsDiv.innerHTML = data.memories.map(m => `
                    <div class="alert alert-info memory-card">
                        <strong>[${{m.id}}]</strong> ${{m.canonical_summary || m.content}}
                        <br><small class="text-muted">匹配度：${{m.score ? m.score.toFixed(2) : 'N/A'}}</small>
                    </div>
                `).join('');
            }} else {{
                resultsDiv.innerHTML = '<div class="alert alert-warning">未找到相关记忆</div>';
            }}
        }}
        
        async function loadRecentMemories() {{
            const response = await fetch('/api/long-term?limit=10');
            const data = await response.json();
            
            const div = document.getElementById('recentMemories');
            if (data.memories && data.memories.length > 0) {{
                div.innerHTML = data.memories.map(m => `
                    <div class="border-bottom py-2">
                        <strong>[${{m.id}}]</strong> ${{m.content.substring(0, 100)}}...
                        <br><small class="text-muted">${{m.created_at}}</small>
                    </div>
                `).join('');
            }} else {{
                div.innerHTML = '<p class="text-muted">暂无记忆</p>';
            }}
        }}
        
        loadRecentMemories();
        </script>
        """

    async def start(self):
        """启动 WebUI 服务"""
        # 检查端口是否被占用
        if is_port_in_use(self.host, self.requested_port):
            logger.warning(f"端口 {self.requested_port} 已被占用，尝试查找可用端口...")
            try:
                self.actual_port = find_available_port(self.host, self.requested_port)
                logger.info(f"找到可用端口：{self.actual_port}")
            except RuntimeError as e:
                logger.error(f"无法找到可用端口：{e}")
                raise
        else:
            self.actual_port = self.requested_port
        
        config = Config(
            self.app,
            host=self.host,
            port=self.actual_port,
            log_level="warning"
        )
        self._server = Server(config)
        
        # 在后台启动
        asyncio.create_task(self._server.serve())
        logger.info(f"WebUI 已启动：http://{self.host}:{self.actual_port}")

    async def get_actual_url(self) -> str:
        """获取实际访问 URL"""
        if self.actual_port:
            return f"http://{self.host}:{self.actual_port}"
        return f"http://{self.host}:{self.requested_port}"

    async def stop(self):
        """停止 WebUI 服务"""
        if self._server:
            self._server.should_exit = True
            logger.info("WebUI 已停止")
