# AstrBot Unified Memory Plugin 安装指南

## 📋 安装前检查

### 系统要求

- ✅ **Python**: 3.8 或更高版本
- ✅ **AstrBot**: 3.4.0 - 5.0.0
- ✅ **操作系统**: Windows / Linux / macOS
- ✅ **内存**: 至少 512MB 可用内存

### 前置配置

在 AstrBot WebUI 中确保已配置：

1. **Embedding Provider**（向量嵌入模型）
   - 用于生成长期记忆的向量表示
   - 推荐使用本地模型（如 bge-small-zh）

2. **LLM Provider**（大语言模型）
   - 用于记忆总结和反思
   - 任何支持的 LLM 均可

---

## 📦 安装步骤

### 方法一：通过 AstrBot 插件市场（推荐）

```bash
# 在 AstrBot WebUI 中
1. 打开 插件管理
2. 搜索 "unified_memory"
3. 点击 安装
4. 等待自动安装依赖
```

### 方法二：手动安装

#### 步骤 1：下载插件

```bash
# 克隆仓库
git clone https://github.com/lxfight/astrbot_plugin_unified_memory.git

# 或下载 ZIP 文件并解压
```

#### 步骤 2：复制到插件目录

将插件文件夹移动到 AstrBot 的插件目录：

```
AstrBot/
└── data/
    └── plugins/
        └── astrbot_plugin_unified_memory/
```

#### 步骤 3：安装依赖

```bash
cd astrbot_plugin_unified_memory
pip install -r requirements.txt
```

**依赖说明**：

```txt
# 核心依赖（必需）
faiss-cpu>=1.7.4        # 向量检索（Meta 开源）
rank-bm25>=0.2.2        # 文本检索（轻量级）

# WebUI 依赖（可选）
fastapi>=0.100.0        # Web 框架
uvicorn>=0.23.0         # ASGI 服务器
starlette>=0.27.0       # FastAPI 依赖
jinja2>=3.1.2           # 模板引擎
```

#### 步骤 4：重启 AstrBot

```bash
# 重启 AstrBot 使插件生效
# 方法取决于你的启动方式
```

---

## ⚙️ 配置插件

### 通过 AstrBot WebUI 配置

1. 打开 AstrBot WebUI
2. 进入 **插件管理** > **astrbot_plugin_unified_memory**
3. 点击 **配置**
4. 修改以下配置（可选）：

```json
{
  "embedding_provider_id": "",  // 留空使用默认
  "llm_provider_id": "",        // 留空使用默认
  "memory_settings": {
    "short_term": {
      "max_messages": 50,       // 短期记忆容量
      "summary_threshold": 10,  // 触发总结的阈值
      "enabled": true
    },
    "long_term": {
      "top_k": 5,              // 检索返回数量
      "auto_summary": true,    // 自动总结
      "forgetting_enabled": true,
      "forgetting_threshold_days": 30
    }
  },
  "webui_settings": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8080,
    "access_password": ""
  }
}
```

5. 点击 **保存**

### 配置文件位置

```
AstrBot/
└── data/
    └── config/
        └── astrbot_plugin_unified_memory.json
```

---

## ✅ 验证安装

### 1. 检查插件状态

在 AstrBot WebUI 中查看：

- 插件是否显示在 **已安装插件** 列表
- 状态是否为 **已启用**
- 是否有错误日志

### 2. 测试命令

在 AstrBot 中发送：

```
/umem help
```

应返回帮助信息：

```
统一记忆插件 - 帮助信息

命令列表:
  /umem status              - 查看记忆库状态
  /umem short               - 查看短期记忆
  /umem long [query]        - 查看/搜索长期记忆
  /umem edit <id> <content> - 编辑指定记忆
  /umem delete <id>         - 删除指定记忆
  /umem search <query> [k]  - 搜索记忆
  /umem clear               - 清除当前会话记忆
  /umem webui               - 查看 WebUI 信息
  /umem help                - 显示帮助
```

### 3. 查看状态

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

检索器状态:
- BM25 文档：0 条
- 向量索引：0 条

系统状态：✅ 已初始化
```

### 4. 访问 WebUI（如果启用）

打开浏览器访问：

```
http://127.0.0.1:8080
```

应看到记忆管理界面。

---

## 🔍 故障排除

### 问题 1：插件无法加载

**症状**：AstrBot 日志显示插件加载失败

**解决方案**：

```bash
# 1. 检查依赖
pip list | grep faiss
pip list | grep bm25

# 2. 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 3. 查看完整错误日志
# 在 AstrBot 日志中搜索 "astrbot_plugin_unified_memory"
```

### 问题 2：命令无响应

**症状**：发送 `/umem` 命令没有反应

**解决方案**：

1. 确认命令前缀正确（使用 `/` 不是 `!`）
2. 检查 AstrBot 命令处理器是否正常
3. 确认插件已启用

### 问题 3：WebUI 无法访问

**症状**：浏览器无法连接到 8080 端口

**解决方案**：

```bash
# 1. 检查端口占用
# Windows
netstat -ano | findstr 8080

# Linux/Mac
lsof -i :8080

# 2. 修改端口
# 在配置中修改 webui_settings.port 为其他值

# 3. 检查防火墙
# 确保允许 8080 端口
```

### 问题 4：Embedding 错误

**症状**：日志显示 "Embedding Provider 未配置"

**解决方案**：

1. 在 AstrBot WebUI 配置 Embedding Provider
2. 确保 Embedding 模型可用
3. 在插件配置中指定 `embedding_provider_id`

### 问题 5：与 AstrBot 冲突

**症状**：插件加载后 AstrBot 异常

**解决方案**：

1. 查看 [COMPATIBILITY.md](./COMPATIBILITY.md) 确认版本兼容
2. 更新到最新版本的插件
3. 在配置中禁用冲突功能

---

## 📊 性能优化

### 内存优化

对于资源受限的环境：

```json
{
  "memory_settings": {
    "short_term": {
      "max_messages": 20,  // 减少短期记忆容量
      "summary_threshold": 5
    },
    "long_term": {
      "top_k": 3  // 减少检索数量
    }
  }
}
```

### 检索优化

对于大量记忆的场景：

```json
{
  "retrieval_settings": {
    "use_hybrid": true,
    "bm25_weight": 0.4,
    "vector_weight": 0.6
  }
}
```

---

## 🔄 更新插件

### 自动更新（如果支持）

在 AstrBot WebUI 中：
1. 插件管理
2. 找到 unified_memory
3. 点击 **更新**

### 手动更新

```bash
# 1. 进入插件目录
cd data/plugins/astrbot_plugin_unified_memory

# 2. 拉取最新代码
git pull

# 3. 更新依赖
pip install -r requirements.txt --upgrade

# 4. 重启 AstrBot
```

---

## 📝 卸载插件

### 通过 WebUI 卸载

1. AstrBot WebUI > 插件管理
2. 找到 unified_memory
3. 点击 **卸载**

### 手动卸载

```bash
# 1. 删除插件目录
rm -rf data/plugins/astrbot_plugin_unified_memory

# 2. 删除配置（可选）
rm data/config/astrbot_plugin_unified_memory.json

# 3. 删除数据（可选）
rm -rf data/plugins/astrbot_plugin_unified_memory/data/

# 4. 重启 AstrBot
```

---

## 🆘 获取帮助

### 文档

- [README.md](./README.md) - 项目说明
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始
- [COMPATIBILITY.md](./COMPATIBILITY.md) - 兼容性说明

### 社区支持

- **GitHub Issues**: https://github.com/lxfight/astrbot_plugin_unified_memory/issues
- **讨论区**: https://github.com/lxfight/astrbot_plugin_unified_memory/discussions

### 提交 Bug

请提供以下信息：

1. AstrBot 版本
2. Python 版本
3. 操作系统
4. 完整的错误日志
5. 复现步骤

---

## ✅ 安装检查清单

安装完成后请确认：

- [ ] 插件在 AstrBot 中显示为"已启用"
- [ ] `/umem help` 命令返回帮助信息
- [ ] `/umem status` 显示正常状态
- [ ] WebUI 可以访问（如果启用）
- [ ] 没有错误日志
- [ ] 可以正常添加和检索记忆

全部通过后，插件即可正常使用！
