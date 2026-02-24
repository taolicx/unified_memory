# AstrBot Plugin Unified Memory - 统一记忆插件

## 📌 功能概述

**Unified Memory** 是一个结合了 **LivingMemory** 和 **Mnemosyne** 优势的综合性记忆插件，为 AstrBot 提供完整的记忆管理能力。

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

### 步骤 1：复制插件

将插件文件夹放置于 AstrBot 的 `data/plugins` 目录下：

```
data/
└── plugins/
    └── astrbot_plugin_unified_memory/
```

### 步骤 2：安装依赖

AstrBot 将自动安装 `requirements.txt` 中的依赖，或手动运行：

```bash
cd data/plugins/astrbot_plugin_unified_memory
pip install -r requirements.txt
```

### 步骤 3：配置 Provider

在 AstrBot WebUI 中配置：
- **Embedding Provider**：用于生成向量嵌入
- **LLM Provider**：用于记忆总结

---

## ⚙️ 配置方式

通过 AstrBot 控制台的**插件配置页面**进行配置：

### 必需配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `embedding_provider_id` | 向量嵌入模型 ID | 留空使用默认 |
| `llm_provider_id` | 大语言模型 ID | 留空使用默认 |

### 记忆配置

```json
{
  "memory_settings": {
    "short_term": {
      "max_messages": 50,        // 短期记忆最大消息数
      "summary_threshold": 10,   // 触发总结的消息阈值
      "enabled": true            // 是否启用短期记忆
    },
    "long_term": {
      "top_k": 5,                // 检索返回的记忆数量
      "auto_summary": true,      // 是否自动总结
      "forgetting_enabled": true,// 是否启用遗忘机制
      "forgetting_threshold_days": 30  // 遗忘阈值（天）
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

---

## 🔧 使用方法

### 命令系统

| 命令 | 说明 | 示例 |
|------|------|------|
| `/umem status` | 查看记忆库状态 | `/umem status` |
| `/umem short` | 查看短期记忆 | `/umem short` |
| `/umem long [query]` | 查看/搜索长期记忆 | `/umem long` 或 `/umem long 天气` |
| `/umem edit <id> <content>` | 编辑指定记忆 | `/umem edit 123 这是修改后的内容` |
| `/umem delete <id>` | 删除指定记忆 | `/umem delete 123` |
| `/umem search <query> [k]` | 搜索记忆 | `/umem search 今天天气 5` |
| `/umem clear` | 清除当前会话记忆 | `/umem clear` |
| `/umem webui` | 查看 WebUI 信息 | `/umem webui` |
| `/umem help` | 显示帮助 | `/umem help` |

### WebUI 管理面板

**访问地址**: http://127.0.0.1:8080（默认端口）

**功能**:
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
astrbot_plugin_unified_memory/
├── main.py                          # 插件入口
├── metadata.yaml                    # 插件元数据
├── _conf_schema.json                # 配置 schema
├── requirements.txt                 # 依赖
├── core/
│   ├── base/                        # 基础组件
│   │   ├── config.py               # 配置管理
│   │   ├── constants.py            # 常量定义
│   │   └── exceptions.py           # 异常定义
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

### 双通道总结

| 通道 | 用途 | 特点 |
|------|------|------|
| `canonical_summary` | 检索用 | 事实导向，结构化，便于相似度匹配 |
| `persona_summary` | 注入用 | 人格风格，自然语言，便于对话融合 |

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
| **许可证** | AGPL-3.0 |
| **主要语言** | Python |
| **向量检索** | Faiss |
| **文本检索** | BM25 |
| **数据库** | SQLite |
| **Web 框架** | FastAPI |

---

## 🔗 使用说明

1. **首次使用**：
   - 确保已配置 Embedding Provider 和 LLM Provider
   - 插件会自动初始化数据库和索引

2. **日常使用**：
   - 插件会自动捕获对话并管理记忆
   - 使用命令或 WebUI 查看和管理记忆

3. **记忆编辑**：
   - 通过 WebUI 可以可视化编辑任何记忆
   - 使用 `/umem edit` 命令快速编辑

4. **性能优化**：
   - 定期使用 `/umem status` 检查记忆库状态
   - 大量记忆时可使用搜索功能快速定位

---

## 📝 更新日志

### v1.0.0
- 初始版本发布
- 整合 LivingMemory 和 Mnemosyne 核心功能
- 支持短期记忆和长期记忆
- 提供 WebUI 管理界面
- 实现混合检索（BM25 + 向量）
- 支持智能总结和自动遗忘

---

## 🙏 致谢

本插件整合了以下优秀插件的功能：
- [astrbot_plugin_livingmemory](https://github.com/lxfight-s-Astrbot-Plugins/astrbot_plugin_livingmemory)
- [astrbot_plugin_mnemosyne](https://github.com/lxfight/astrbot_plugin_mnemosyne)

感谢原作者的精彩工作！
