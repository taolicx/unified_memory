# 🚀 快速安装 - Unified Memory 插件

## ⚡ 3 分钟快速安装

### 步骤 1：下载插件（30 秒）

```bash
# 方法 A：Git 克隆
git clone https://github.com/lxfight/astrbot_plugin_unified_memory.git

# 方法 B：下载 ZIP 解压
# 访问 https://github.com/lxfight/astrbot_plugin_unified_memory/archive/refs/heads/main.zip
```

### 步骤 2：移动到插件目录（30 秒）

```
将 astrbot_plugin_unified_memory 文件夹移动到：

AstrBot/data/plugins/astrbot_plugin_unified_memory/
```

### 步骤 3：安装依赖（1 分钟）

```bash
cd astrbot_plugin_unified_memory
pip install -r requirements.txt
```

**依赖说明**：
- `faiss-cpu` - Meta 开源向量检索（常见）
- `rank-bm25` - 标准文本检索（常见）
- `fastapi` - Web 框架（常见）
- `uvicorn` - ASGI 服务器（常见）
- `starlette` - FastAPI 依赖（常见）
- `jinja2` - 模板引擎（常见）

### 步骤 4：重启 AstrBot（30 秒）

```bash
# 重启你的 AstrBot
```

---

## ✅ 验证安装

### 测试 1：检查插件状态

在 AstrBot WebUI 中：
- 插件管理 → 已安装插件
- 应看到 `astrbot_plugin_unified_memory`
- 状态应为 **已启用**

### 测试 2：发送测试命令

在 AstrBot 中发送：

```
/umem help
```

应返回帮助信息。

### 测试 3：查看状态

发送：

```
/umem status
```

应返回：
```
📊 记忆库状态

短期记忆：0 条
长期记忆：0 条
会话数量：0 个
```

### 测试 4：访问 WebUI（可选）

浏览器打开：
```
http://127.0.0.1:8080
```

---

## ⚙️ 基本配置

### 必需配置

在 AstrBot WebUI 中确保已配置：

1. **Embedding Provider** - 向量嵌入模型
2. **LLM Provider** - 大语言模型

### 可选配置

插件配置路径：
```
AstrBot WebUI → 插件管理 → astrbot_plugin_unified_memory → 配置
```

推荐配置：
```json
{
  "embedding_provider_id": "",  // 留空使用默认
  "llm_provider_id": "",        // 留空使用默认
  "memory_settings": {
    "short_term": {
      "max_messages": 50,
      "enabled": true
    },
    "long_term": {
      "top_k": 5,
      "auto_summary": true
    }
  },
  "webui_settings": {
    "enabled": true,
    "port": 8080
  }
}
```

---

## 🎯 常用命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `/umem help` | 显示帮助 | `/umem help` |
| `/umem status` | 查看状态 | `/umem status` |
| `/umem short` | 短期记忆 | `/umem short` |
| `/umem long` | 长期记忆 | `/umem long` |
| `/umem search 关键词` | 搜索记忆 | `/umem search 天气` |
| `/umem webui` | WebUI 地址 | `/umem webui` |

---

## ❓ 常见问题

### Q: 依赖安装失败？

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 端口 8080 被占用？

插件会**自动检测**并切换到可用端口（8081、8082 等）

查看实际端口：
```
/umem webui
```

### Q: 命令无响应？

1. 确认使用 `/` 前缀（不是 `!`）
2. 确认插件已启用
3. 查看 AstrBot 日志

### Q: 与 AstrBot 冲突？

**不会冲突！** 插件已进行全面的兼容性优化：
- ✅ 使用通用事件处理
- ✅ 独立命令命名空间
- ✅ 端口冲突自动检测
- ✅ 支持 AstrBot 3.4-5.0

---

## 📚 详细文档

- `README.md` - 项目说明
- `INSTALL.md` - 详细安装指南
- `QUICKSTART.md` - 快速开始
- `COMPATIBILITY.md` - 兼容性说明
- `FIXES_SUMMARY.md` - 修复总结

---

## 🆘 获取帮助

**GitHub Issues**: https://github.com/lxfight/astrbot_plugin_unified_memory/issues

提交 Issue 时请提供：
1. AstrBot 版本
2. Python 版本
3. 错误日志
4. 复现步骤

---

**安装完成！开始使用吧！** 🎉
