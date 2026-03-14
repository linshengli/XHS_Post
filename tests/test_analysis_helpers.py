from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_script_module(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_like_count_supports_wan_suffix():
    module = load_script_module("analyze_trending", "scripts/02_analyze_trending.py")

    assert module.parse_like_count("4.2万") == 42000
    assert module.parse_like_count("6800") == 6800
    assert module.parse_like_count("") == 0


def test_filter_posts_by_source_keyword_matches_core_topic():
    module = load_script_module("analyze_trending_topic", "scripts/02_analyze_trending.py")
    posts = [
        {"source_keyword": "千岛湖", "title": "千岛湖旅游攻略", "desc": "", "tag_list": ""},
        {"source_keyword": "北京", "title": "北京旅游攻略", "desc": "", "tag_list": ""},
    ]

    filtered = module.filter_posts_by_source_keyword(posts, "千岛湖旅游攻略")

    assert len(filtered) == 1
    assert filtered[0]["source_keyword"] == "千岛湖"

