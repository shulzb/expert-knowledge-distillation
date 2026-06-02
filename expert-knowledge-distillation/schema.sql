-- 专家认知蒸馏系统 · 数据库建表
-- SQLite 3

-- 数据源表
CREATE TABLE IF NOT EXISTS sources (
    id          TEXT PRIMARY KEY,          -- 如 'xiaoe_liurun'
    name        TEXT NOT NULL,             -- '刘润进化岛'
    platform    TEXT NOT NULL,             -- 'xiaoe' / 'weixin' / 'xiaohongshu'
    expert_name TEXT NOT NULL,             -- '刘润' / '润宇'
    description TEXT DEFAULT '',
    config_json TEXT DEFAULT '{}',
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- 帖子表（核心表）
CREATE TABLE IF NOT EXISTS posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   TEXT NOT NULL REFERENCES sources(id),
    post_id     TEXT NOT NULL,             -- 第三方平台ID
    title       TEXT DEFAULT '',
    content     TEXT NOT NULL DEFAULT '',  -- 清洗后的纯文本正文
    raw_content TEXT DEFAULT '',           -- 原始 HTML/JSON
    summary     TEXT DEFAULT '',           -- LLM 生成摘要
    url         TEXT DEFAULT '',
    author_name TEXT DEFAULT '',           -- 发布者昵称
    author_role TEXT DEFAULT '',           -- 圈主/会员等
    tags        TEXT DEFAULT '[]',         -- JSON数组 ["刘润日课", "AI"]
    is_picked   INTEGER DEFAULT 0,         -- 是否精选
    comment_cnt INTEGER DEFAULT 0,
    like_cnt    INTEGER DEFAULT 0,
    share_cnt   INTEGER DEFAULT 0,
    published_at TEXT DEFAULT '',          -- 发布时间
    fetched_at  TEXT DEFAULT (datetime('now')),
    is_extracted INTEGER DEFAULT 0,        -- 是否已知识提取
    UNIQUE(source_id, post_id)
);
CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source_id);
CREATE INDEX IF NOT EXISTS idx_posts_pubdate ON posts(published_at);
CREATE INDEX IF NOT EXISTS idx_posts_extracted ON posts(is_extracted);

-- 知识单元表（提取后的结构化知识）
CREATE TABLE IF NOT EXISTS knowledge_units (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id     INTEGER NOT NULL REFERENCES posts(id),
    unit_type   TEXT NOT NULL,             -- 'concept' / 'argument' / 'logic_chain' / 'case' / 'quote' / 'style'
    title       TEXT DEFAULT '',
    content     TEXT NOT NULL DEFAULT '',
    keywords    TEXT DEFAULT '[]',         -- JSON数组 关键词
    confidence  REAL DEFAULT 0.8,
    extracted_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_knowledge_post ON knowledge_units(post_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_units(unit_type);

-- 概念表（跨文章的归一化概念）
CREATE TABLE IF NOT EXISTS concepts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    category    TEXT DEFAULT '',
    description TEXT DEFAULT '',
    aliases     TEXT DEFAULT '[]',
    created_at  TEXT DEFAULT (datetime('now'))
);

-- 概念-帖子关联表
CREATE TABLE IF NOT EXISTS concept_posts (
    concept_id  INTEGER NOT NULL REFERENCES concepts(id),
    post_id     INTEGER NOT NULL REFERENCES posts(id),
    sentiment   TEXT DEFAULT '',           -- 'positive' / 'negative' / 'neutral'
    view_point  TEXT DEFAULT '',
    PRIMARY KEY (concept_id, post_id)
);

-- 写作风格分析表
CREATE TABLE IF NOT EXISTS writing_style (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   TEXT NOT NULL REFERENCES sources(id),
    dimension   TEXT NOT NULL,             -- 'vocabulary' / 'sentence_pattern' / 'rhetoric' / 'structure'
    feature     TEXT NOT NULL DEFAULT '',
    examples    TEXT DEFAULT '[]',
    frequency   REAL DEFAULT 0.0,
    analyzed_at TEXT DEFAULT (datetime('now'))
);

-- 观点演变追踪表
CREATE TABLE IF NOT EXISTS view_evolution (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id     TEXT NOT NULL REFERENCES sources(id),
    topic         TEXT NOT NULL,
    view_stages   TEXT NOT NULL DEFAULT '[]',  -- JSON: [{date, view, intensity}]
    trend         TEXT DEFAULT '',
    last_analyzed TEXT DEFAULT (datetime('now'))
);

-- FTS5 全文搜索虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
    title, content, summary, tags,
    content='posts', content_rowid='id',
    tokenize='unicode61'
);
