#!/usr/bin/env python3
"""单元测试：xhs_post.topic 模块 - 关键词扩展和主题过滤。"""

import pytest
from xhs_post.topic import (
    KEYWORD_EXPANSION,
    GENERIC_WORDS,
    expand_keywords,
    extract_core_topics,
    filter_posts_by_source_keyword,
    filter_posts_by_topic,
    parse_like_count,
)


class TestKeywordExpansion:
    """测试关键词扩展功能。"""

    def test_keyword_expansion_exists(self):
        """测试关键词扩展配置存在。"""
        assert "亲子" in KEYWORD_EXPANSION
        assert "酒店" in KEYWORD_EXPANSION
        assert "骑行" in KEYWORD_EXPANSION
        assert "美食" in KEYWORD_EXPANSION

    def test_qinzi_expansion(self):
        """测试"亲子"关键词扩展。"""
        keywords = expand_keywords("亲子游")
        assert "亲子" in keywords
        assert "带娃" in keywords
        assert "遛娃" in keywords
        assert "儿童" in keywords

    def test_jiudian_expansion(self):
        """测试"酒店"关键词扩展。"""
        keywords = expand_keywords("千岛湖酒店")
        assert "酒店" in keywords
        assert "住宿" in keywords
        assert "民宿" in keywords
        assert "度假村" in keywords

    def test_topic_itself_included(self):
        """测试主题本身包含在扩展结果中。"""
        keywords = expand_keywords("千岛湖骑行")
        assert "千岛湖骑行" in keywords or "千岛湖" in keywords

    def test_no_duplicates(self):
        """测试扩展结果无重复。"""
        keywords = expand_keywords("亲子酒店")
        assert len(keywords) == len(set(keywords))

    def test_custom_topic_expansion(self):
        """测试自定义主题扩展。"""
        keywords = expand_keywords("北京美食探店")
        # 应该包含"美食"相关扩展
        assert any(kw in keywords for kw in ["美食", "餐厅", "小吃", "探店"])


class TestGenericWords:
    """测试通用词过滤。"""

    def test_generic_words_exists(self):
        """测试通用词配置存在。"""
        assert "攻略" in GENERIC_WORDS
        assert "指南" in GENERIC_WORDS
        assert "推荐" in GENERIC_WORDS

    def test_generic_words_filtered(self):
        """测试通用词在过滤时被排除。"""
        # GENERIC_WORDS 应该用于过滤，不作为核心关键词
        for word in GENERIC_WORDS:
            assert len(word) <= 2 or word in ["攻略", "指南", "推荐", "教程", "分享", "心得", "体验", "日记", "玩法", "超全", "详细", "必看", "路线"]


class TestExtractCoreTopics:
    """测试核心主题提取功能。"""

    def test_preset_city_detected(self):
        """测试预设城市被识别。"""
        assert extract_core_topics("千岛湖旅行") == ["千岛湖"]
        assert extract_core_topics("西双版纳游玩") == ["西双版纳"]
        assert extract_core_topics("北京美食") == ["北京"]

    def test_unknown_topic_default(self):
        """测试未知主题返回前两个字。"""
        assert extract_core_topics("未知地点") == ["未知"]
        assert extract_core_topics("东京迪士尼") == ["东京"]

    def test_exact_match_priority(self):
        """测试精确匹配优先级。"""
        # "杭州"应该优先匹配预设，而不是返回"杭州"
        assert extract_core_topics("杭州西湖") == ["杭州"]


class TestFilterPostsBySourceKeyword:
    """测试按 source_keyword 过滤帖子。"""

    def test_exact_source_keyword_match(self):
        """测试精确匹配 source_keyword。"""
        posts = [
            {"source_keyword": "千岛湖亲子酒店", "title": "标题 1"},
            {"source_keyword": "其他主题", "title": "标题 2"},
        ]
        result = filter_posts_by_source_keyword(posts, "千岛湖")
        assert len(result) == 1
        assert result[0]["title"] == "标题 1"

    def test_partial_source_keyword_match(self):
        """测试部分匹配 source_keyword。"""
        posts = [
            {"source_keyword": "千岛湖亲子酒店", "title": "标题 1"},
        ]
        result = filter_posts_by_source_keyword(posts, "千岛湖")
        assert len(result) == 1

    def test_fallback_to_text_search(self):
        """测试 source_keyword 缺失时回退到文本搜索。"""
        posts = [
            {"source_keyword": "", "title": "千岛湖旅行", "desc": "", "tag_list": ""},
            {"source_keyword": "", "title": "其他内容", "desc": "", "tag_list": ""},
        ]
        result = filter_posts_by_source_keyword(posts, "千岛湖")
        assert len(result) == 1
        assert result[0]["title"] == "千岛湖旅行"

    def test_empty_posts_list(self):
        """测试空帖子列表。"""
        result = filter_posts_by_source_keyword([], "千岛湖")
        assert len(result) == 0

    def test_no_match_returns_empty(self):
        """测试无匹配返回空列表。"""
        posts = [
            {"source_keyword": "北京", "title": "北京内容"},
            {"source_keyword": "上海", "title": "上海内容"},
        ]
        result = filter_posts_by_source_keyword(posts, "广州")
        assert len(result) == 0


class TestFilterPostsByTopic:
    """测试按主题关键词过滤帖子。"""

    def test_keyword_in_title(self):
        """测试标题包含关键词。"""
        posts = [
            {"title": "千岛湖亲子酒店推荐", "desc": "", "tag_list": ""},
            {"title": "其他内容", "desc": "", "tag_list": ""},
        ]
        result = filter_posts_by_topic(posts, ["千岛湖", "亲子"])
        assert len(result) == 1

    def test_keyword_in_desc(self):
        """测试描述包含关键词。"""
        posts = [
            {"title": "标题", "desc": "这是关于千岛湖的内容", "tag_list": ""},
            {"title": "标题 2", "desc": "其他内容", "tag_list": ""},
        ]
        result = filter_posts_by_topic(posts, ["千岛湖"])
        assert len(result) == 1

    def test_keyword_in_tags(self):
        """测试标签包含关键词。"""
        posts = [
            {"title": "", "desc": "", "tag_list": "#千岛湖#亲子游"},
            {"title": "", "desc": "", "tag_list": "#其他"},
        ]
        result = filter_posts_by_topic(posts, ["千岛湖"])
        assert len(result) == 1

    def test_generic_words_filtered(self):
        """测试通用词被过滤。"""
        posts = [
            {"title": "攻略分享", "desc": "", "tag_list": ""},  # 只有通用词
        ]
        # "攻略"和"分享"都是 GENERIC_WORDS，应该被过滤
        result = filter_posts_by_topic(posts, ["攻略", "分享"])
        assert len(result) == 0

    def test_multiple_keywords_match(self):
        """测试多关键词匹配。"""
        posts = [
            {"title": "千岛湖酒店", "desc": "", "tag_list": ""},
            {"title": "千岛湖美食", "desc": "", "tag_list": ""},
        ]
        result = filter_posts_by_topic(posts, ["酒店"])
        assert len(result) == 1

    def test_empty_keywords_list(self):
        """测试空关键词列表。"""
        posts = [
            {"title": "任何内容", "desc": "", "tag_list": ""},
        ]
        result = filter_posts_by_topic(posts, [])
        assert len(result) == 0


class TestParseLikeCount:
    """测试点赞数解析功能。"""

    def test_plain_number(self):
        """测试纯数字解析。"""
        assert parse_like_count("100") == 100
        assert parse_like_count("9999") == 9999

    def test_wan_unit(self):
        """测试"万"单位解析。"""
        assert parse_like_count("1 万") == 10000
        assert parse_like_count("2.5 万") == 25000
        assert parse_like_count("10 万") == 100000

    def test_whitespace_handling(self):
        """测试空白字符处理。"""
        assert parse_like_count("  100  ") == 100
        assert parse_like_count(" 1 万 ") == 10000

    def test_invalid_input(self):
        """测试无效输入处理。"""
        assert parse_like_count(None) == 0
        assert parse_like_count("") == 0
        assert parse_like_count("abc") == 0
        assert parse_like_count("1.2.3") == 0

    def test_integer_result(self):
        """测试结果总是整数。"""
        result = parse_like_count("1.5 万")
        assert isinstance(result, int)
        assert result == 15000


class TestTopicWorkflow:
    """测试主题相关工作流。"""

    def test_expand_and_filter_integration(self):
        """测试关键词扩展和过滤集成。"""
        topic = "千岛湖亲子酒店"
        
        # 1. 扩展关键词
        keywords = expand_keywords(topic)
        assert len(keywords) > 0
        
        # 2. 准备测试数据
        posts = [
            {
                "source_keyword": "千岛湖亲子酒店",
                "title": "千岛湖带娃入住这家酒店太值了",
                "desc": "亲子设施齐全，有儿童乐园",
                "tag_list": "#千岛湖#亲子游#酒店推荐"
            },
            {
                "source_keyword": "其他主题",
                "title": "北京美食攻略",
                "desc": "",
                "tag_list": ""
            }
        ]
        
        # 3. 按 source_keyword 过滤
        filtered_by_source = filter_posts_by_source_keyword(posts, topic)
        assert len(filtered_by_source) == 1
        
        # 4. 按关键词过滤
        filtered_by_topic = filter_posts_by_topic(filtered_by_source, keywords)
        assert len(filtered_by_topic) == 1

    def test_deduplication_scenario(self):
        """测试去重场景。"""
        # 模拟两个非常相似的帖子
        posts = [
            {"title": "千岛湖亲子酒店", "desc": "内容 A", "tag_list": ""},
            {"title": "千岛湖亲子酒店", "desc": "内容 A", "tag_list": ""},  # 重复
        ]
        
        keywords = ["千岛湖", "亲子", "酒店"]
        result = filter_posts_by_topic(posts, keywords)
        
        # 过滤器不会去重，两个都会保留
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
