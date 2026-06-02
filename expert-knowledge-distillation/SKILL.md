---
title: "distill-system"
summary: "专家认知蒸馏系统 - 数据导入、知识提取、搜索问答（刘润+润宇+精算视觉）"
agent_created: true
read_when:
  - 用户提到"蒸馏"、"知识库"、"刘润"、"专家"、"搜索知识"
  - 用户说"搜一下刘润怎么说"、"查一下刘润的观点"
  - 用户说"问问刘润"、"用刘润风格回答"
  - 用户说"知识蒸馏"、"distill"
  - 用户说"跑蒸馏系统"、"跑全部流程"
  - 用户说"润宇入库"、"导入润宇"
---

# distill-system - 专家认知蒸馏系统

> 此文件为代码目录文档副本。最新技能定义在:
> `~/.workbuddy/skills/distill-system/SKILL.md`

## 数据统计（截至 2026-06-02）

| 数据源 | 帖子 | 已提取 | 最新 |
|--------|------|--------|------|
| 刘润进化岛 | 644 | 644 ✅ | 2026-06-01 |
| 润宇创业笔记 | 321 | 321 ✅ | 2026-06-02 |
| 精算视觉公众号 | 100 | 100 ✅ | 2026-05-28 |
| **合计** | **1,065** | **1,065** | - |

知识单元: **9,130** | ChromaDB 向量: **10,171**

## 目录结构

```
~/.workbuddy/distill-system/
├── run.py                       ← 总入口
├── schema.sql                   ← 数据库建表
├── db/database.py               ← SQLite + FTS5
├── collectors/xiaoe_collector.py ← 小鹅通采集器
├── pipeline/
│   ├── extraction_pipeline.py   ← 知识提取（DeepSeek API）
│   └── data_ingest.py           ← 数据导入
├── query/
│   ├── cmd_query.py             ← CLI 查询工具
│   ├── search_engine.py         ← FTS+语义混合搜索
│   └── vector_store.py          ← ChromaDB 向量检索
├── persona/                     ← AI人格化问答
└── scripts/                     ← 辅助脚本
```

## 快速命令

```bash
cd ~/.workbuddy/distill-system
python run.py stats          # 统计
python run.py search "关键词" # 搜索
python run.py ask "问题"     # AI问答
python run.py chat           # 交互对话
```
