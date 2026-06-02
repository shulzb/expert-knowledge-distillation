# 专家认知蒸馏系统 (Expert Knowledge Distillation System)

> 从精选内容（付费社群、公众号等）中提取结构化知识，构建可检索、可问答的专家级知识库。

## 它能做什么

```
原始内容（帖子/文章/视频）
    ↓ 采集器（Collector）
结构化数据（SQLite + FTS5 全文索引）
    ↓ LLM 知识提取
知识单元（概念/逻辑链/论点/摘要）
    ↓ 向量嵌入（ChromaDB）
语义检索 + AI 人格化问答
```

## 核心特性

- **多数据源** — 支持小鹅通圈子、微信公众号、自定义 Markdown/JSON
- **增量采集** — 只拉取新内容，不重复
- **LLM 知识提取** — 使用 DeepSeek/GPT API，从每篇文章中提取：
  - 核心概念（含定义）
  - 逻辑链条（推理过程）
  - 判断模式（条件→结论）
  - 摘要+核心论点
- **混合搜索** — FTS5 全文搜索 + ChromaDB 语义搜索，双引擎加持
- **向量联合检索** — 同时搜索原文 + 知识单元，精度更高
- **AI 人格化问答** — 基于 RAG 管道，回答引用原文和知识单元

## 快速开始

### 1️⃣ 安装依赖

```bash
pip install requests chromadb
```

### 2️⃣ 配置 API

```bash
# 复制模板配置
cp config/llm_config.template.json config/llm_config.json

# 编辑 config/llm_config.json，填入你的 API Key
```

### 3️⃣ 添加数据源

参考 `collectors/xiaoe_collector.py` 中的 `SOURCES` 配置：

```python
SOURCES = {
    'my_source': {
        'name': '我的数据源',
        'platform': 'xiaoe',   # 或 'weixin', 'json', 'markdown'
        'expert_name': '专家名',
        'description': '描述',
    },
}
```

### 4️⃣ 数据导入 & 提取

```bash
# 统计
python run.py stats

# 搜索
python run.py search "关键词"

# AI 问答
python run.py ask "你的问题"

# 交互对话
python run.py chat
```

## 项目结构

```
distill-system/
├── run.py                    # 主入口（stats/search/ask/chat）
├── schema.sql                # 数据库结构
├── collectors/               # 数据采集器
│   ├── base_collector.py     # 基类
│   └── xiaoe_collector.py    # 小鹅通圈子采集器
├── db/
│   └── database.py           # SQLite + FTS5 操作
├── pipeline/
│   ├── data_ingest.py        # 数据导入
│   └── extraction_pipeline.py # 知识提取（LLM）
├── query/
│   ├── search_engine.py      # 混合搜索
│   ├── vector_store.py       # ChromaDB 向量存储
│   └── cmd_query.py          # CLI 查询
├── persona/                  # AI 人格化层
│   ├── rag_pipeline.py       # RAG 管道
│   ├── prompt_builder.py     # Prompt 组装
│   └── persona_chat.py       # 对话式问答
├── scripts/                  # 辅助脚本
│   ├── batch_extract.py      # 批量知识提取
│   └── embed_knowledge_units.py # 向量嵌入
└── config/                   # 配置（已 gitignore）
    └── llm_config.template.json
```

## 数据库结构

| 表 | 用途 |
|---|---|
| `sources` | 数据源注册 |
| `posts` | 原始帖子（含 FTS5 全文索引） |
| `knowledge_units` | 知识单元（concept/logic_chain/argument/summary） |
| `concepts` | 跨文章概念归一化 |
| `writing_style` | 写作风格分析 |
| `view_evolution` | 观点演变追踪 |

## 自定义数据源

要实现自己的数据源，继承 `BaseCollector`：

```python
from collectors.base_collector import BaseCollector

class MyCollector(BaseCollector):
    def fetch_posts(self, since_id=None, limit=50):
        # 返回标准化帖子列表
        pass
    
    def fetch_full_content(self, post_id):
        # 获取完整内容
        pass
```

详见 `collectors/base_collector.py`。

## LICENSE

MIT
