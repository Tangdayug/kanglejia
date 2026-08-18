import logging
import os
import re
from pathlib import Path
from typing import List, Optional

import markdown
from fastapi import HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api import app

logger = logging.getLogger(__name__)


# 定义数据模型
class Article(BaseModel):
    id: int
    title: str
    type: str  # 'article' 或 'video'
    category: str
    summary: str
    content: Optional[str] = None
    videoUrl: Optional[str] = None
    coverImage: Optional[str] = None
    tags: List[str] = []
    createdAt: str

# 后端目录
BACKEND_DIR = Path(__file__).parent.parent
ARTICLES_DIR = BACKEND_DIR
VIDEOS_DIR = BACKEND_DIR

# 科普内容配置
EDUCATION_CONTENTS = [
    {
        "id": 1,
        "title": "两大能力决定健康走向",
        "type": "article",
        "category": "mental",
        "summary": "内在能力和生活能力是预示衰老轨迹的关键指标。专家解读如何通过维护这两大能力，延缓衰老，提升生活质量。",
        "tags": ["内在能力", "生活能力", "衰老", "健康"],
        "file": "宣医科普两大能力决定健康走向.md"
    },
    {
        "id": 2,
        "title": "守护内在能力，老了不遭罪",
        "type": "article",
        "category": "rehabilitation",
        "summary": "通过日常四大场景（厨房、卧室、浴室、户外）的干预，守护老年人的自理能力，延缓内在能力衰退。",
        "tags": ["内在能力", "自理能力", "康复训练", "日常护理"],
        "file": "守护内在能力_老了不遭罪.md"
    },
    {
        "id": 3,
        "title": "老年人运动指导（一）",
        "type": "video",
        "category": "exercise",
        "summary": "适合老年人的温和运动教程，帮助提升心肺功能和身体灵活性。",
        "tags": ["运动", "健康", "教程", "有氧运动"],
        "file": "1.mp4"
    },
    {
        "id": 4,
        "title": "老年人运动指导（二）",
        "type": "video",
        "category": "exercise",
        "summary": "更多适合老年人的简单运动，包括力量训练和平衡训练。",
        "tags": ["运动", "力量训练", "平衡", "健康"],
        "file": "2.mp4"
    }
]


def parse_markdown_file(filepath: Path) -> str:
    """解析 Markdown 文件为 HTML"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 转换为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )

        return html_content
    except Exception as e:
        logger.warning(f"解析 Markdown 失败: {e}")
        return ""


@app.get("/health-education/list", response_model=List[Article])
async def get_articles():
    """获取科普内容列表"""
    articles = []

    for item in EDUCATION_CONTENTS:
        file_path = ARTICLES_DIR / item["file"]

        # 解析文章内容
        content = None
        video_url = None

        if item["type"] == "article":
            if file_path.exists():
                content = parse_markdown_file(file_path)
        else:  # video
            video_url = f"/health-education/video/{item['id']}"

        article = Article(
            id=item["id"],
            title=item["title"],
            type=item["type"],
            category=item["category"],
            summary=item["summary"],
            content=content,
            videoUrl=video_url,
            tags=item["tags"],
            createdAt="2025-01-01"
        )
        articles.append(article)

    return articles


@app.get("/health-education/article/{article_id}", response_model=Article)
async def get_article_detail(article_id: int):
    """获取文章详情"""
    article_config = next((item for item in EDUCATION_CONTENTS if item["id"] == article_id), None)

    if not article_config:
        raise HTTPException(status_code=404, detail="文章不存在")

    file_path = ARTICLES_DIR / article_config["file"]

    content = None
    video_url = None

    if article_config["type"] == "article":
        if file_path.exists():
            content = parse_markdown_file(file_path)
    else:  # video
        video_url = f"/health-education/video/{article_id}"

    return Article(
        id=article_config["id"],
        title=article_config["title"],
        type=article_config["type"],
        category=article_config["category"],
        summary=article_config["summary"],
        content=content,
        videoUrl=video_url,
        tags=article_config["tags"],
        createdAt="2025-01-01"
    )


@app.get("/health-education/video/{video_id}")
async def get_video(video_id: int):
    """获取视频文件"""
    article_config = next(
        (item for item in EDUCATION_CONTENTS
         if item["id"] == video_id and item["type"] == "video"),
        None
    )

    if not article_config:
        raise HTTPException(status_code=404, detail="视频不存在")

    file_path = VIDEOS_DIR / article_config["file"]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name
    )
