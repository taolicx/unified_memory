# AstrBot Plugin Unified Memory - 统一记忆插件

[![GitHub](https://img.shields.io/github/license/taolicx/unified_memory)](https://github.com/taolicx/unified_memory)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4.0--5.0.0-green.svg)](https://github.com/Soulter/AstrBot)
[![GitHub stars](https://img.shields.io/github/stars/taolicx/unified_memory)](https://github.com/taolicx/unified_memory/stargazers)

**AstrBot Unified Memory** 是一个结合了 **LivingMemory** 和 **Mnemosyne** 优势的综合性记忆插件，为 AstrBot 提供完整的记忆管理能力。

---

## 📌 功能概述

### 核心特性

| 特性 | 说明 |
|------|------|
| **双通道记忆** | 短期记忆（工作记忆）+ 长期记忆（持久化存储） |
| **混合检索** | BM25 稀疏检索 + Faiss 向量检索 + RRF 融合算法 |
| **智能总结** | 使用 LLM 自动总结对话，生成结构化记忆 |
| **WebUI 管理** | 可视化记忆管理界面，支持编辑、删除、搜索 |
| **会话隔离** | 支持按人格和会话隔离记忆 |
| **自动遗忘** | 基于时间和重要性的智能清理机制 |

---

## 📦 安装方法

### 方法一：Git 安装（推荐）

```bash
# 进入 AstrBot 插件目录
cd AstrBot/data/plugins

# 克隆仓库
git clone https://github.com/taolicx/unified_memory.git

# 安装依赖
cd unified_memory
pip install -r requirements.txt

# 重启 AstrBot
```

**更新插件**：
```bash
cd AstrBot/data/plugins/unified_memory
git pull
pip install -r requirements.txt --upgrade
```

### 方法二：手动安装

1. **下载插件**
   - 访问 https://github.com/taolicx/unified_memory
   - 点击 **Code** → **Download ZIP**
   - 解压到 `AstrBot/data/plugins/` 目录

2. **安装依赖**
   ```bash
   cd AstrBot/data/plugins/unified_memory
   pip install -r requirements.txt
   ```

3. **重启 AstrBot**

### 方法三：通过 AstrBot WebUI（如果支持）

1. 打开 AstrBot WebUI
2. 进入 **插件管理**
3. 搜索 `unified_memory`
4. 点击 **安装**

---

## ⚙️ 配置方式

通过 AstrBot 控制台的**插件配置页面**进行配置：

### 必需配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `embedding_provider_id` | 向量嵌入模型 ID | 留空使用默认 |
| `llm_provider_id` | 大语言模型 ID | 留空使用默认 |

### 完整配置示例

```json
{
  "embedding_provider_id": "",
  "llm_provider_id": "",
  "memory_settings": {
    "short_term": {
      "max_messages": 50,
      "summary_threshold": 10,
      "enabled": true
    },
    "long_term": {
      "top_k": 5,
      "auto_summary": true,
      "forgetting_enabled": true,
      "forgetting_threshold_days": 30
    }
  },
  "webui_settings": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8080,
    "access_password": ""
  },
  "retrieval_settings": {
    "use_hybrid": true,
    "bm25_weight": 0.5,
    "vector_weight": 0.5
  }
}
```

### 配置项说明

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| `max_messages` | 短期记忆最大消息数 | 50 |
| `summary_threshold` | 触发总结的消息阈值 | 10 |
| `top_k` | 检索返回的记忆数量 | 5 |
| `forgetting_threshold_days` | 遗忘阈值（天） | 30 |
| `port` | WebUI 访问端口 | 8080 |

---

## 🔧 使用方法

### 命令系统

| 命令 | 说明 | 示例 |
|------|------|------|
| `/umem status` | 查看记忆库状态 | `/umem status` |
| `/umem short` | 查看短期记忆 | `/umem short` |
| `/umem long [query]` | 查看/搜索长期记忆 | `/umem long` 或 `/umem long 天气` |
| `/umem edit <id> <content>` | 编辑指定记忆 | `/umem edit 123 新内容` |
| `/umem delete <id>` | 删除指定记忆 | `/umem delete 123` |
| `/umem search <query> [k]` | 搜索记忆 | `/umem search 今天天气 5` |
| `/umem clear` | 清除当前会话记忆 | `/umem clear` |
| `/umem webui` | 查看 WebUI 信息 | `/umem webui` |
| `/umem help` | 显示帮助 | `/umem help` |

### WebUI 管理面板

**访问地址**: http://127.0.0.1:8080（默认端口）

**功能模块**:
- 📊 **首页统计**：查看短期/长期记忆数量和会话统计
- ⚡ **短期记忆**：查看和管理短期工作记忆
- 🗄️ **长期记忆**：查看、编辑、删除长期记忆
- 🔍 **搜索记忆**：使用关键词搜索相关记忆
- 📈 **统计分析**：记忆使用统计和趋势分析
- ⚙️ **设置**：插件配置管理

**API 接口**:

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stats` | GET | 获取统计信息 |
| `/api/short-term` | GET | 获取短期记忆列表 |
| `/api/long-term` | GET | 获取长期记忆列表 |
| `/api/memory/{id}` | GET/PUT/DELETE | 获取/更新/删除单条记忆 |
| `/api/search?query=xxx` | GET | 搜索记忆 |
| `/api/memory` | POST | 创建新记忆 |
| `/api/sessions` | GET | 获取所有会话 |

---

## 🏗️ 核心架构

```
unified_memory/
├── main.py                          # 插件入口
├── metadata.yaml                    # 插件元数据
├── _conf_schema.json                # 配置 schema
├── requirements.txt                 # 依赖
├── core/
│   ├── base/                        # 基础组件
│   │   ├── config.py               # 配置管理
│   │   ├── constants.py            # 常量定义
│   │   ├── exceptions.py           # 异常定义
│   │   └── api_adapter.py          # AstrBot API 适配器
│   ├── managers/
│   │   ├── memory_engine.py        # 记忆引擎核心
│   │   └── conversation_manager.py # 会话管理
│   ├── retrieval/
│   │   ├── bm25.py                 # BM25 检索
│   │   └── hybrid_retriever.py     # 混合检索器
│   ├── summarizer/
│   │   └── memory_summarizer.py    # 记忆总结器
│   ├── event_handler.py            # 事件处理器
│   └── command_handler.py          # 命令处理器
├── storage/
│   ├── database.py                 # SQLite 数据库
│   └── faiss_index.py              # Faiss 索引
├── webui/
│   └── app.py                      # Web 应用
└── tests/                          # 测试套件
```

---

## 🧠 记忆实现原理

### 短期记忆（Short-term Memory）

- **存储位置**: 内存 + SQLite
- **容量限制**: 可配置（默认 50 条消息）
- **自动总结**: 达到阈值后自动转为长期记忆
- **用途**: 当前对话上下文的快速访问

### 长期记忆（Long-term Memory）

- **存储位置**: SQLite + Faiss 向量索引
- **检索方式**: 混合检索（BM25 + 向量）
- **智能遗忘**: 基于时间和重要性自动清理
- **用途**: 持久化知识存储

### 记忆流转

```
新对话 → 短期记忆 → 达到阈值 → LLM 总结 → 长期记忆
                              ↓
                         定期反思 → 重要性评估 → 遗忘机制
```

### 混合检索流程

```
用户查询 → BM25 稀疏检索 → ┐
                           ├→ RRF 融合算法 → 排序结果
用户查询 → Faiss 向量检索 → ┘
```

---

## 📊 技术规格

| 项目 | 信息 |
|-----|------|
| **版本** | 1.0.0 |
| **许可证** | MIT |
| **主要语言** | Python |
| **向量检索** | Faiss |
| **文本检索** | BM25 |
| **数据库** | SQLite |
| **Web 框架** | FastAPI |
| **AstrBot 版本** | 3.4.0 - 5.0.0 |

---

## 📖 文档

- [📥 快速安装](QUICK_INSTALL.md) - 3 分钟快速开始
- [📚 详细安装指南](INSTALL.md) - 完整安装和配置
- [🔧 兼容性说明](COMPATIBILITY.md) - 兼容性保证
- [📝 修复报告](COMPATIBILITY_REPORT.md) - 技术细节
- [📤 Git 上传指南](GIT_UPLOAD.md) - 如何贡献代码

---

## 🔗 相关链接

- **GitHub**: https://github.com/taolicx/unified_memory
- **Issues**: https://github.com/taolicx/unified_memory/issues
- **AstrBot**: https://github.com/Soulter/AstrBot

---

## 🙏 致谢

本插件整合了以下优秀插件的功能：
- [astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory)
- [astrbot_plugin_mnemosyne](https://github.com/lxfight/astrbot_plugin_mnemosyne)

感谢原作者的精彩工作！

---

## 📝 更新日志

### v1.0.0 (2026-02-24)
- ✨ 初始版本发布
- 🔧 整合 LivingMemory 和 Mnemosyne 核心功能
- 🧠 支持短期记忆和长期记忆
- 🌐 提供 WebUI 管理界面
- 🔍 实现混合检索（BM25 + 向量）
- 🤖 支持智能总结和自动遗忘
- ✅ 全面兼容性优化（AstrBot 3.4.0-5.0.0）

---

**作者**: taolicx  
**许可证**: MIT License
