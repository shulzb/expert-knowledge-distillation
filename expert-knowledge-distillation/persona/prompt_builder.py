#!/usr/bin/env python3
"""
distill-system: prompt_builder.py
AI Persona Prompt 组装器
"""

import json
from typing import List, Dict, Optional


class PersonaPromptBuilder:
    """构建专家人格的 System Prompt"""

    def __init__(self, expert_name: str = '刘润', source_id: str = 'xiaoe_liurun'):
        self.expert_name = expert_name
        self.source_id = source_id

    def build_system_prompt(self, context: str = '',
                            style_traits: List[str] = None,
                            logic_chains: List[str] = None,
                            opinions: List[Dict] = None) -> str:
        """组装完整的 System Prompt"""
        parts = []

        # 1. 角色设定
        parts.append(f"""## 角色设定
你是{self.expert_name}的AI知识助手。

你的知识库基于{self.expert_name}公开发布的内容（刘润日课等）。
回答时请模拟{self.expert_name}的思维方式、表达风格和判断逻辑。

## 核心原则
- 基于知识库内容回答，不编造{self.expert_name}没有说过的话
- 如果问题超出知识范围，明确说明"我的知识库中暂无对此的论述"
- 可以引用具体日课日期来增强可信度
- 保持回答简洁、有洞察力，避免套话""")

        # 2. 表达风格
        if style_traits:
            parts.append("## 表达风格参考")
            for s in style_traits:
                parts.append(f"- {s}")

        # 3. 判断框架
        if logic_chains:
            parts.append("""## 核心思维框架""")
            for lc in logic_chains:
                parts.append(f"- {lc}")

        # 4. 观点参考
        if opinions:
            parts.append("""## 已知观点（供参考）""")
            for op in opinions:
                topic = op.get('topic', '')
                stance = op.get('stance', '')
                if topic and stance:
                    parts.append(f"- 关于「{topic}」：{stance}")

        # 5. 格式要求
        parts.append("""## 回答格式
- 先给出直接答案或观点
- 然后简要说明推理过程
- 最后可引用相关出处
- 总体不超过500字""")

        return '\n\n'.join(parts)

    def build_rag_query(self, user_question: str, context_posts: List[Dict],
                        knowledge_units: List[Dict] = None) -> str:
        """构建 RAG 查询的 User Prompt"""
        parts = [f"用户问题：{user_question}", "", "## 参考材料：", ""]

        # 帖子参考
        if context_posts:
            parts.append("--- 相关文章 ---")
            for i, post in enumerate(context_posts[:5], 1):
                title = post.get('title', '') or '(无标题)'
                pub = (post.get('published_at', '') or '')[:10]
                content = (post.get('content', '') or '')[:800]
                parts.append(f"\n[文章 {i}] [{pub}] {title}\n{content}")

        # 知识单元参考
        if knowledge_units:
            parts.append("\n--- 相关知识片段（精炼的观点/概念/逻辑链） ---")
            for i, ku in enumerate(knowledge_units[:6], 1):
                meta = ku.get('metadata', {})
                utype = meta.get('unit_type', 'knowledge')
                distance = ku.get('distance', 0)
                # 从 DB 获取完整内容
                uid = meta.get('unit_id', 0)
                if uid:
                    content = self._get_ku_content(uid)
                else:
                    content = ''
                label = {'concept': '概念', 'argument': '观点', 'logic_chain': '逻辑链',
                         'case': '案例', 'quote': '引语', 'summary': '摘要'}.get(utype, utype)
                parts.append(f"\n[{label} {i}] (相关度: {1-distance:.2f})\n{content[:500]}")

        parts.append(f"""
请基于以上参考材料回答用户问题。
回答要体现{self.expert_name}的风格和思维方式，引用具体内容支撑观点。
""")

        return '\n'.join(parts)

    @staticmethod
    def _get_ku_content(unit_id: int) -> str:
        """从 SQLite 获取知识单元完整内容"""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from db.database import get_conn
            conn = get_conn()
            row = conn.execute(
                "SELECT content, title, keywords FROM knowledge_units WHERE id=?",
                (unit_id,)
            ).fetchone()
            conn.close()
            if row:
                title = row['title'] or ''
                content = row['content'] or ''
                keywords = row['keywords'] or ''
                if title:
                    return f"{title}: {content}"
                return content
        except Exception:
            pass
        return ''
