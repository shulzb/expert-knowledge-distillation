#!/usr/bin/env python3
"""
distill-system: 采集器抽象基类
定义统一接口：所有数据源采集器继承此类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseCollector(ABC):
    """采集器基类"""

    def __init__(self, source_id: str):
        self.source_id = source_id

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称（如 '刘润进化岛'）"""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型（xiaoe / weixin / xiaohongshu）"""
        ...

    @abstractmethod
    def fetch_posts(self, since_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        获取帖子列表，返回标准化后的帖子 dict 列表。
        since_id: 增量更新的起点（上次最后一条的 post_id）
        """
        ...

    @abstractmethod
    def fetch_full_content(self, post_id: str) -> str:
        """获取单条帖子的完整正文（非截断）"""
        ...

    def normalize_post(self, raw: Dict) -> Dict:
        """
        将原始 API 响应标准化为统一格式。
        子类可重写此方法来适配不同平台的数据格式。
        """
        return {
            'post_id': raw.get('post_id', ''),
            'title': raw.get('title', ''),
            'content': raw.get('content', ''),
            'raw_content': raw.get('raw_content', ''),
            'url': raw.get('url', ''),
            'author_name': raw.get('author_name', ''),
            'author_role': raw.get('author_role', ''),
            'tags': raw.get('tags', '[]'),
            'is_picked': raw.get('is_picked', 0),
            'comment_cnt': raw.get('comment_cnt', 0),
            'like_cnt': raw.get('like_cnt', 0),
            'share_cnt': raw.get('share_cnt', 0),
            'published_at': raw.get('published_at', ''),
        }
