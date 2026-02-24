# AstrBot 插件兼容性说明

## ✅ 兼容性保证

本插件已进行全面的兼容性测试和优化，确保与 AstrBot 无缝集成。

---

## 🔧 依赖优化

### 核心依赖（必需）

| 依赖 | 版本 | 用途 | 说明 |
|------|------|------|------|
| `faiss-cpu` | >=1.7.4 | 向量检索 | Meta 开源的向量相似度搜索库 |
| `rank-bm25` | >=0.2.2 | 文本检索 | 轻量级 BM25 文本检索算法 |

### WebUI 依赖（可选）

| 依赖 | 版本 | 用途 | 说明 |
|------|------|------|------|
| `fastapi` | >=0.100.0 | Web 框架 | 现代高性能 Web 框架 |
| `uvicorn` | >=0.23.0 | ASGI 服务器 | 高性能异步服务器 |
| `starlette` | >=0.27.0 | Web 工具 | FastAPI 底层依赖 |
| `jinja2` | >=3.1.2 | 模板引擎 | WebUI 模板渲染 |

### 已移除的依赖

以下依赖已移除，避免与 AstrBot 冲突：

- ❌ `httpx` - 使用 AstrBot 内置 HTTP 客户端
- ❌ `aiofiles` - 使用标准库异步文件操作
- ❌ `python-dotenv` - 使用 AstrBot 配置系统

---

## 🔌 AstrBot 版本兼容

### 支持的版本

| AstrBot 版本 | 兼容性 | 说明 |
|-------------|--------|------|
| 3.4.x | ✅ 完全兼容 | 最低支持版本 |
| 3.5.x | ✅ 完全兼容 | |
| 4.0.x | ✅ 完全兼容 | |
| 4.1.x | ✅ 完全兼容 | |
| 5.0.x | ✅ 完全兼容 | 最高支持版本 |

### API 适配器

插件内置 `AstrBotAPIAdapter`，自动适配不同版本的 API 差异：

```python
from .core.base import api_adapter

# 自动检测版本
api_adapter.detect_version()

# 使用兼容方式注册事件
api_adapter.register_event_handler(plugin, "on_message", handler)

# 使用兼容方式注册命令
api_adapter.register_command(plugin, ["umem"], handler)
```

---

## ⚠️ 避免冲突的设计

### 1. 命令命名空间

所有命令使用 `umem_` 前缀，避免与 AstrBot 和其他插件冲突：

- `/umem` - 主命令
- `/umem_status` - 查看状态
- `/umem_short` - 短期记忆
- `/umem_long` - 长期记忆
- `/umem_search` - 搜索
- `/umem_edit` - 编辑
- `/umem_delete` - 删除
- `/umem_clear` - 清除
- `/umem_webui` - WebUI 信息

### 2. 事件处理

使用通用事件类型，避免与平台特定事件冲突：

```python
# ✅ 正确：使用通用事件
plugin.register_event_handler("on_message", self.on_message)

# ❌ 错误：避免使用平台特定事件
# plugin.register_event_handler("group_message", ...)
```

### 3. 数据存储

- **数据库文件**: 存储在 `data/plugins/astrbot_plugin_unified_memory/` 目录
- **Faiss 索引**: 存储在独立的 `faiss_index/` 子目录
- **日志**: 使用 `astrbot_plugin_unified_memory` 命名空间，避免日志混淆

### 4. 配置隔离

所有配置项都在独立的配置命名空间下：

```json
{
  "embedding_provider_id": "",
  "llm_provider_id": "",
  "memory_settings": {...},
  "webui_settings": {...},
  "retrieval_settings": {...}
}
```

---

## 🛠️ 故障排除

### 问题：插件无法加载

**解决方案**：
1. 检查依赖是否安装：`pip list | grep faiss`
2. 查看 AstrBot 日志中的错误信息
3. 确认配置项完整

### 问题：命令无响应

**解决方案**：
1. 确认命令前缀正确（`/umem` 不是 `!umem`）
2. 检查 AstrBot 命令处理器是否正常
3. 查看插件日志：`logger.info("命令已注册")`

### 问题：WebUI 无法访问

**解决方案**：
1. 检查端口是否被占用：`netstat -ano | findstr 8080`
2. 确认防火墙设置
3. 检查配置中的 `host` 和 `port`

### 问题：与 AstrBot 核心功能冲突

**解决方案**：
1. 更新到最新版本的插件
2. 检查 AstrBot 版本是否在支持范围内
3. 在插件配置中禁用冲突功能

---

## 📋 安装检查清单

安装前请确认：

- [ ] AstrBot 版本 >= 3.4.0
- [ ] Python 版本 >= 3.8
- [ ] 已配置 Embedding Provider
- [ ] 已配置 LLM Provider
- [ ] 插件目录权限正确

安装后请验证：

- [ ] 插件成功加载（查看日志）
- [ ] 命令可用（`/umem help`）
- [ ] WebUI 可访问（如果启用）
- [ ] 记忆功能正常

---

## 🔒 安全保证

### 数据安全

- ✅ 所有数据本地存储（SQLite + Faiss）
- ✅ 不上传任何数据到外部服务器
- ✅ 支持数据导出和备份

### 权限控制

- ✅ WebUI 支持访问密码
- ✅ 命令基于会话隔离
- ✅ 记忆按用户/会话隔离

---

## 📞 技术支持

如遇到兼容性问题：

1. 查看日志文件定位问题
2. 检查 AstrBot 和插件版本
3. 在 GitHub 提交 Issue（附上日志）

**GitHub**: https://github.com/lxfight/astrbot_plugin_unified_memory
