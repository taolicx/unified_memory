# AstrBot Plugin Unified Memory - 快速开始指南

## 🚀 快速安装

### 1. 安装插件

将 `astrbot_plugin_unified_memory` 文件夹复制到 AstrBot 的插件目录：

```
data/plugins/astrbot_plugin_unified_memory/
```

### 2. 安装依赖

```bash
cd data/plugins/astrbot_plugin_unified_memory
pip install -r requirements.txt
```

### 3. 配置 Provider

在 AstrBot WebUI 中确保已配置：
- ✅ Embedding Provider（用于向量嵌入）
- ✅ LLM Provider（用于记忆总结）

### 4. 重启 AstrBot

重启后插件将自动初始化。

---

## 📖 基本使用

### 查看记忆状态

```
/umem status
```

输出示例：
```
📊 记忆库状态

短期记忆：15 条
长期记忆：42 条
会话数量：8 个

检索器状态:
- BM25 文档：42 条
- 向量索引：42 条

系统状态：✅ 已初始化
```

### 查看短期记忆

```
/umem short
```

显示当前会话的短期工作记忆。

### 查看长期记忆

```
/umem long
```

显示当前会话的长期记忆。

### 搜索记忆

```
/umem search 天气
```

搜索与"天气"相关的记忆。

### 编辑记忆

```
/umem edit 123 这是修改后的内容
```

将 ID 为 123 的记忆内容修改为新内容。

### 删除记忆

```
/umem delete 123
```

删除 ID 为 123 的记忆。

### 清除会话记忆

```
/umem clear
```

清除当前会话的所有短期记忆。

---

## 🌐 WebUI 使用

### 访问 WebUI

在浏览器中打开：
```
http://127.0.0.1:8080
```

如果修改了端口，请使用配置的端口号。

### WebUI 功能

#### 首页
- 查看记忆统计（短期/长期记忆数量、会话数）
- 快速搜索记忆
- 查看最近记忆

#### 短期记忆管理
- 查看所有短期记忆
- 按会话过滤
- 删除不需要的记忆

#### 长期记忆管理
- 查看所有长期记忆
- 编辑记忆内容
- 删除记忆
- 查看记忆详情（包括总结内容）

#### 搜索功能
- 关键词搜索
- 混合检索（BM25 + 向量）
- 按相关性排序

#### 统计分析
- 记忆增长趋势
- 会话分布
- 检索统计

---

## ⚙️ 高级配置

### 短期记忆配置

```json
{
  "short_term": {
    "max_messages": 50,        // 最大消息数
    "summary_threshold": 10,   // 达到此数量自动总结
    "enabled": true            // 是否启用
  }
}
```

**建议**：
- 频繁对话场景：`max_messages: 100`, `summary_threshold: 20`
- 低频对话场景：`max_messages: 30`, `summary_threshold: 5`

### 长期记忆配置

```json
{
  "long_term": {
    "top_k": 5,                     // 检索返回数量
    "auto_summary": true,           // 自动总结
    "forgetting_enabled": true,     // 启用遗忘
    "forgetting_threshold_days": 30 // 30 天以上的记忆可能被遗忘
  }
}
```

**建议**：
- 需要更多上下文：`top_k: 10`
- 精确检索：`top_k: 3`
- 永久记忆：`forgetting_enabled: false`

### 检索配置

```json
{
  "retrieval_settings": {
    "use_hybrid": true,      // 使用混合检索
    "bm25_weight": 0.5,      // BM25 权重
    "vector_weight": 0.5     // 向量检索权重
  }
}
```

**建议**：
- 关键词匹配重要：`bm25_weight: 0.7`, `vector_weight: 0.3`
- 语义匹配重要：`bm25_weight: 0.3`, `vector_weight: 0.7`

---

## 🔧 故障排除

### 问题：插件无法启动

**检查**：
1. 依赖是否安装完整：`pip install -r requirements.txt`
2. Provider 是否已配置
3. 查看 AstrBot 日志

### 问题：记忆无法检索

**解决**：
1. 检查 Embedding Provider 是否正常工作
2. 使用 `/umem status` 检查检索器状态
3. 尝试重建索引（需要添加此命令）

### 问题：WebUI 无法访问

**检查**：
1. 端口是否被占用
2. 防火墙设置
3. 配置中的 host 是否为 `127.0.0.1`

### 问题：总结质量不佳

**优化**：
1. 更换更强大的 LLM Provider
2. 调整 `summary_threshold` 增加上下文
3. 手动编辑不满意的总结

---

## 📝 最佳实践

### 1. 定期清理
- 每周查看一次记忆库
- 删除无关或过时的记忆
- 使用 WebUI 批量管理

### 2. 合理配置
- 根据使用频率调整记忆容量
- 平衡检索速度和准确性
- 定期备份重要记忆

### 3. 会话管理
- 为不同场景使用不同会话
- 定期清理不活跃会话
- 使用会话隔离保护隐私

### 4. 性能优化
- 大量记忆时启用混合检索
- 定期重建索引保持性能
- 监控内存使用情况

---

## 🆘 获取帮助

### 命令帮助
```
/umem help
```

### 查看文档
- README.md - 完整文档
- QUICKSTART.md - 快速开始

### 技术支持
如遇问题，请提供：
1. AstrBot 版本
2. 插件版本
3. 错误日志
4. 配置信息（隐藏敏感数据）

---

## 📚 示例场景

### 场景 1：个人助手

**配置**：
```json
{
  "short_term": {"max_messages": 100, "summary_threshold": 20},
  "long_term": {"top_k": 10, "forgetting_enabled": false}
}
```

**用途**：记住用户偏好、习惯、重要日期

### 场景 2：客服机器人

**配置**：
```json
{
  "short_term": {"max_messages": 50, "summary_threshold": 10},
  "long_term": {"top_k": 5, "forgetting_enabled": true}
}
```

**用途**：记录客户问题、解决方案、服务历史

### 场景 3：多用户环境

**配置**：
```json
{
  "short_term": {"max_messages": 30, "summary_threshold": 5},
  "long_term": {"top_k": 3},
  "session_isolation": true
}
```

**用途**：为每个用户维护独立记忆空间

---

祝你使用愉快！🎉
