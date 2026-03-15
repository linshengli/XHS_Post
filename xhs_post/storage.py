from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(file_path: Path) -> dict[str, Any]:
    """加载 JSON 文件，出错时返回空字典并记录日志。"""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败 {file_path}: {e}")
        return {}
    except IOError as e:
        logger.error(f"文件读取失败 {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"未知错误加载 {file_path}: {e}")
        return {}


def save_json(file_path: Path, data: dict[str, Any]) -> bool:
    """保存 JSON 文件，成功返回 True，失败返回 False 并记录日志。"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logger.error(f"文件写入失败 {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"未知错误保存 {file_path}: {e}")
        return False


def load_jsonl_files(input_dir: Path) -> list[dict[str, Any]]:
    """加载目录下所有 JSONL 文件，跳过无效行。"""
    posts: list[dict[str, Any]] = []
    if not input_dir.exists():
        return posts

    for file_path in sorted(input_dir.glob("*.jsonl")):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        posts.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSONL 解析失败 {file_path}:{line_num}: {e}")
        except IOError as e:
            logger.error(f"无法读取文件 {file_path}: {e}")
            continue

    return posts


def seed_file_from_legacy(target_path: Path, legacy_path: Path, default_data: dict[str, Any] | None = None) -> None:
    """从旧路径迁移文件，如果目标已存在则跳过。"""
    if target_path.exists():
        return
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if legacy_path.exists():
        try:
            shutil.copyfile(legacy_path, target_path)
            logger.info(f"已从 {legacy_path} 迁移到 {target_path}")
        except IOError as e:
            logger.error(f"文件迁移失败 {legacy_path} -> {target_path}: {e}")
            if default_data is not None:
                save_json(target_path, default_data)
        return
    if default_data is not None:
        save_json(target_path, default_data)


def mirror_json_to_legacy(source_path: Path, legacy_path: Path) -> None:
    """同步 JSON 文件到旧路径。"""
    if not source_path.exists():
        return
    try:
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, legacy_path)
    except IOError as e:
        logger.error(f"文件同步失败 {source_path} -> {legacy_path}: {e}")
