from __future__ import annotations

import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from xhs_post.dedup import build_content_signature, find_similar_signature
from xhs_post.images import select_crawled_images_for_post
from xhs_post.llm import generate_structured_post
from xhs_post.models import LLMPostWorkflowRequest
from xhs_post.storage import load_json, load_jsonl_files, save_json
from xhs_post.topic import expand_keywords, filter_posts_by_source_keyword

logger = logging.getLogger(__name__)

# 全局配置缓存
_config_cache: dict[str, Any] = {}
_config_loaded = False


def _load_config(base_dir: Path) -> dict[str, Any]:
    """加载配置文件，使用缓存避免重复读取。"""
    global _config_cache, _config_loaded
    if _config_loaded:
        return _config_cache
    
    config_file = base_dir / "config.yaml"
    if config_file.exists():
        try:
            _config_cache = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            logger.debug(f"已加载配置文件：{config_file}")
        except Exception as e:
            logger.warning(f"加载配置文件失败：{e}，使用默认配置")
            _config_cache = {}
    else:
        logger.debug("未找到配置文件，使用默认配置")
        _config_cache = {}
    
    _config_loaded = True
    return _config_cache


def _get_angles(topic: str, base_dir: Path) -> list[str]:
    """获取角度列表，支持按主题定制。"""
    config = _load_config(base_dir)
    generation_config = config.get("generation", {})
    
    # 检查是否有针对该主题的配置
    topic_angles = generation_config.get("topic_angles", {})
    for topic_key, angles in topic_angles.items():
        if topic_key in topic:
            logger.debug(f"使用主题 '{topic_key}' 的角度配置")
            return angles
    
    # 使用默认角度
    default_angles = generation_config.get("default_angles", [
        "保姆级攻略",
        "避坑指南",
        "实测体验",
        "本地人推荐",
        "带娃攻略"
    ])
    logger.debug(f"使用默认角度配置：{len(default_angles)} 个")
    return default_angles


def _get_prompt_template(base_dir: Path) -> str:
    """获取提示词模板。"""
    config = _load_config(base_dir)
    prompts = config.get("prompts", {})
    
    template = prompts.get("post_generation")
    if template:
        logger.debug("使用配置文件中的提示词模板")
        return template
    
    # 默认模板
    logger.debug("使用默认提示词模板")
    return "\n".join([
        "请输出 JSON，包含 title, content, tags 三个字段。",
        "主题：{topic}",
        "角度：{angle}",
        "价值点：{value_points}",
        "场景：{scenes}",
        "参考标签：{tags}",
        "要求：标题 20 字以内；正文适合小红书图文；tags 返回数组。",
    ])


def _get_posting_times(base_dir: Path) -> list[str]:
    """获取发布时间选项列表。"""
    config = _load_config(base_dir)
    content_config = config.get("content", {})
    
    times = content_config.get("posting_times")
    if times:
        return times
    
    # 默认发布时间
    return [
        "早上 7:30-9:00 (早高峰)",
        "中午 12:00-14:00 (午休)",
        "晚上 18:00-20:00 (晚高峰)",
        "晚上 21:00-23:00 (睡前)"
    ]


def _build_prompt(topic: str, angle: str, features: dict[str, Any], base_dir: Path) -> str:
    """构建 LLM 提示词，使用配置的模板。"""
    value_points = features.get("value_points", [])[:5]
    scenes = features.get("scenes", [])[:3]
    tags = features.get("tags", [])[:8]
    
    template = _get_prompt_template(base_dir)
    return template.format(
        topic=topic,
        angle=angle,
        value_points=value_points,
        scenes=scenes,
        tags=tags,
    )


def _format_post_markdown(post: dict[str, Any], base_dir: Path) -> str:
    """格式化笔记为 Markdown，使用配置的发布时间选项。"""
    posting_times = _get_posting_times(base_dir)
    
    lines = [
        "# 🔥 标题选项 (1 个)",
        f"1. {post['title']}",
        "",
        "## 🏷️ 推荐标签",
        " ".join(post["tags"]),
        "",
        "## 📸 配图",
    ]
    for index, image in enumerate(post["images"], 1):
        lines.append(f"{index}. [{image['role']}] {image['path']} ({image.get('theme', '未标注')})")
    lines.extend(
        [
            "",
            "## ✍️ 正文",
            "",
            post["content"],
            "",
            "## ⏰ 最佳发布时间",
            random.choice(posting_times),
            "",
            "---",
            f"*生成时间：{datetime.now().isoformat()}*",
            f"*主题：{post['topic']}*",
            f"*角度：{post['angle']}*",
            f"*Provider：{post['provider']}*",
        ]
    )
    return "\n".join(lines)


def run_llm_post_generation_workflow(request: LLMPostWorkflowRequest) -> list[Path]:
    """执行 LLM 笔记生成工作流，包含完整的错误处理和日志记录。"""
    if request.seed is not None:
        random.seed(request.seed)
    
    # 确定基础目录
    base_dir = request.output_dir.parent.parent if request.output_dir.parent.name else Path.cwd()

    # 加载热点分析数据
    trending_data = load_json(request.trending_input)
    if not trending_data:
        logger.warning(f"热点分析文件为空或不存在：{request.trending_input}")
    
    # 加载状态文件
    state = load_json(request.state_file) if request.state_file else {}
    content_signatures = list(state.get("content_signatures", []))
    
    # 加载原始笔记数据
    raw_posts = filter_posts_by_source_keyword(load_jsonl_files(request.raw_posts_dir), request.topic)
    if not raw_posts:
        logger.warning(f"未找到主题 '{request.topic}' 相关的原始笔记")
    
    features = trending_data.get("features", {})
    
    # 从配置加载角度列表
    angles = _get_angles(request.topic, base_dir)
    
    # 创建输出目录
    try:
        request.output_dir.mkdir(parents=True, exist_ok=True)
    except IOError as e:
        logger.error(f"无法创建输出目录 {request.output_dir}: {e}")
        raise

    output_files = []
    for index in range(1, request.count + 1):
        response: dict[str, Any] | None = None
        angle = angles[(index - 1) % len(angles)]
        
        # 尝试生成内容，最多尝试 max_attempts_per_post 次
        for attempt in range(request.max_attempts_per_post):
            angle = angles[(index - 1 + attempt) % len(angles)]
            try:
                candidate = generate_structured_post(
                    _build_prompt(request.topic, angle, features, base_dir),
                    provider=request.provider
                )
            except Exception as e:
                logger.warning(f"生成第 {index} 篇笔记失败 (尝试 {attempt + 1}/{request.max_attempts_per_post}): {e}")
                continue
            
            # 检查重复
            try:
                signature = build_content_signature(candidate["title"], candidate["content"])
                duplicate = find_similar_signature(
                    signature,
                    content_signatures,
                    threshold=request.similarity_threshold,
                )
                if duplicate:
                    logger.debug(f"第 {index} 篇笔记与已有内容重复 (相似度：{duplicate.get('similarity', 'N/A')})")
                    continue
                candidate["_signature"] = signature
                response = candidate
                break
            except KeyError as e:
                logger.warning(f"第 {index} 篇笔记响应格式错误：缺少字段 {e}")
                continue
        
        if response is None:
            error_msg = f"无法生成独特的第 {index} 篇笔记（达到最大尝试次数）"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # 处理标签
        tags = response.get("tags") or [f"#{keyword}" for keyword in expand_keywords(request.topic)[:5]]
        if isinstance(tags, str):
            tags = tags.split()
        
        # 选择配图
        images = select_crawled_images_for_post(raw_posts)
        
        # 构建笔记数据
        content_signatures.append(response["_signature"])
        post = {
            "title": response["title"],
            "content": response["content"],
            "tags": tags,
            "images": images,
            "topic": request.topic,
            "angle": angle,
            "provider": response.get("_provider", request.provider or "unknown"),
        }
        
        # 写入文件
        output_file = request.output_dir / f"{request.topic}_{index:02d}.md"
        try:
            output_file.write_text(_format_post_markdown(post, base_dir), encoding="utf-8")
            logger.info(f"已生成笔记：{output_file.name}")
            output_files.append(output_file)
        except IOError as e:
            logger.error(f"写入笔记文件失败 {output_file}: {e}")
            continue

    # 更新状态文件
    if request.state_file:
        state["content_signatures"] = content_signatures[-200:]
        state["last_generation"] = {
            "topic": request.topic,
            "count": len(output_files),
            "generated_at": datetime.now().isoformat(),
        }
        if not save_json(request.state_file, state):
            logger.error(f"保存状态文件失败：{request.state_file}")

    logger.info(f"生成完成：成功 {len(output_files)}/{request.count} 篇笔记")
    return output_files
