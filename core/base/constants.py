"""
基础组件 - 常量定义
"""

# 记忆类型
MEMORY_TYPE_SHORT_TERM = "short_term"
MEMORY_TYPE_LONG_TERM = "long_term"

# 默认配置
DEFAULT_CONFIG = {
    "embedding_provider_id": "",
    "llm_provider_id": "",
    "memory_settings": {
        "short_term": {
            "max_messages": 50,
            "summary_threshold": 10,
            "enabled": True
        },
        "long_term": {
            "top_k": 5,
            "auto_summary": True,
            "forgetting_enabled": True,
            "forgetting_threshold_days": 30
        }
    },
    "webui_settings": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 8080,
        "access_password": ""
    },
    "retrieval_settings": {
        "use_hybrid": True,
        "bm25_weight": 0.5,
        "vector_weight": 0.5
    }
}

# 数据库表名
TABLE_SHORT_TERM_MEMORIES = "short_term_memories"
TABLE_LONG_TERM_MEMORIES = "long_term_memories"
TABLE_CONVERSATIONS = "conversations"
TABLE_PERSONAS = "personas"

# 记忆状态
MEMORY_STATUS_ACTIVE = "active"
MEMORY_STATUS_ARCHIVED = "archived"
MEMORY_STATUS_DELETED = "deleted"

# 命令前缀
COMMAND_PREFIX = "/umem"

# 帮助信息
HELP_MESSAGE = """
统一记忆插件 - 帮助信息

命令列表:
  {prefix} status              - 查看记忆库状态
  {prefix} short               - 查看短期记忆
  {prefix} long [query]        - 查看/搜索长期记忆
  {prefix} edit <id> <content> - 编辑指定记忆
  {prefix} delete <id>         - 删除指定记忆
  {prefix} search <query> [k]  - 搜索记忆
  {prefix} clear               - 清除当前会话记忆
  {prefix} webui               - 查看 WebUI 信息
  {prefix} help                - 显示帮助

示例:
  {prefix} search 今天天气
  {prefix} edit 123 这是修改后的内容
  {prefix} delete 123
""".strip()

# WebUI 默认模板
WEBUI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>统一记忆管理</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        body { background-color: #f5f5f5; }
        .sidebar { min-height: 100vh; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); }
        .sidebar a { color: white; text-decoration: none; }
        .sidebar a:hover { background-color: rgba(255,255,255,0.1); }
        .content { padding: 20px; }
        .memory-card { border-left: 4px solid #667eea; }
        .memory-card.short-term { border-left-color: #28a745; }
        .memory-card.long-term { border-left-color: #667eea; }
        .stats-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 sidebar p-3">
                <h4 class="text-white mb-4"><i class="bi bi-brain"></i> 统一记忆</h4>
                <nav>
                    <a href="/" class="d-block py-2"><i class="bi bi-house"></i> 首页</a>
                    <a href="/short-term" class="d-block py-2"><i class="bi bi-lightning"></i> 短期记忆</a>
                    <a href="/long-term" class="d-block py-2"><i class="bi bi-database"></i> 长期记忆</a>
                    <a href="/search" class="d-block py-2"><i class="bi bi-search"></i> 搜索记忆</a>
                    <a href="/stats" class="d-block py-2"><i class="bi bi-bar-chart"></i> 统计分析</a>
                    <a href="/settings" class="d-block py-2"><i class="bi bi-gear"></i> 设置</a>
                </nav>
            </div>
            <div class="col-md-10 content">
                {{ content|safe }}
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
