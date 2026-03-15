#!/usr/bin/env python3
"""单元测试：xhs_post.dedup 模块 - 内容去重和相似度检测。"""

import pytest
from xhs_post.dedup import (
    normalize_text,
    build_content_signature,
    content_similarity,
    find_similar_signature,
)


class TestNormalizeText:
    """测试文本标准化函数。"""

    def test_basic_normalization(self):
        """测试基本文本标准化。"""
        assert normalize_text("Hello World") == "hello world"
        # 注意：normalize_text 只替换多个空白为单个空格，不移除中文间的空格
        assert normalize_text("  多 余 空 格  ") == "多 余 空 格"

    def test_case_insensitive(self):
        """测试大小写不敏感。"""
        assert normalize_text("HELLO") == normalize_text("hello")
        assert normalize_text("Hello") == normalize_text("HELLO")

    def test_remove_special_chars(self):
        """测试特殊字符移除。"""
        assert normalize_text("Hello! World?") == "hello world"
        # 注意：#符号被保留（用于 hashtag）
        assert normalize_text("测试@#￥内容") == "测试#内容"

    def test_chinese_text(self):
        """测试中文文本标准化。"""
        # 注意：中文间的空格不会被移除
        assert normalize_text(" 千岛湖 旅行 攻略 ") == "千岛湖 旅行 攻略"
        assert normalize_text("带娃👨‍👩‍👧‍👦出游") == "带娃出游"

    def test_whitespace_normalization(self):
        """测试空白字符标准化。"""
        assert normalize_text("hello\tworld\n") == "hello world"
        assert normalize_text("a  b   c") == "a b c"


class TestBuildContentSignature:
    """测试内容签名构建函数。"""

    def test_signature_structure(self):
        """测试签名结构完整性。"""
        sig = build_content_signature("测试标题", "这是内容")
        assert "title" in sig
        assert "content_preview" in sig
        assert "normalized_title" in sig
        assert "normalized_content" in sig
        assert "combined" in sig

    def test_title_preserved(self):
        """测试标题原始内容保留。"""
        sig = build_content_signature("千岛湖亲子酒店攻略", "内容...")
        assert sig["title"] == "千岛湖亲子酒店攻略"

    def test_content_preview_length(self):
        """测试内容预览长度限制。"""
        long_content = "x" * 200
        sig = build_content_signature("标题", long_content)
        assert len(sig["content_preview"]) <= 120

    def test_normalization_applied(self):
        """测试标准化应用于签名。"""
        sig = build_content_signature("  标题  ", "  内容  ")
        assert sig["normalized_title"] == "标题"
        assert sig["normalized_content"] == "内容"


class TestContentSimilarity:
    """测试内容相似度计算函数。"""

    def test_identical_content(self):
        """测试完全相同内容的相似度。"""
        sig1 = build_content_signature("相同标题", "相同内容")
        sig2 = build_content_signature("相同标题", "相同内容")
        similarity = content_similarity(sig1, sig2)
        assert similarity == 1.0

    def test_completely_different(self):
        """测试完全不同内容的相似度。"""
        sig1 = build_content_signature("标题 A", "内容 A")
        sig2 = build_content_signature("标题 B", "内容 B")
        similarity = content_similarity(sig1, sig2)
        # 由于标题和内容的归一化，完全不同内容的相似度可能在 0.5-0.8 之间
        assert similarity < 0.8

    def test_similar_title_different_content(self):
        """测试标题相似但内容不同的相似度。"""
        sig1 = build_content_signature("千岛湖攻略", "内容 A")
        sig2 = build_content_signature("千岛湖攻略", "内容 B 完全不同")
        similarity = content_similarity(sig1, sig2)
        # 标题权重 0.35，内容权重 0.65
        # 标题完全相同 (1.0 * 0.35) + 内容部分相似
        assert 0.35 <= similarity < 0.8

    def test_different_title_similar_content(self):
        """测试标题不同但内容相似的相似度。"""
        sig1 = build_content_signature("标题 A", "这是很长的相同内容" * 10)
        sig2 = build_content_signature("标题 B", "这是很长的相同内容" * 10)
        similarity = content_similarity(sig1, sig2)
        assert similarity > 0.5

    def test_whitespace_insensitive(self):
        """测试空白字符不影响相似度。"""
        sig1 = build_content_signature("标题", "内容")
        sig2 = build_content_signature("  标题  ", "  内容  ")
        similarity = content_similarity(sig1, sig2)
        assert similarity == 1.0

    def test_case_insensitive(self):
        """测试大小写不影响相似度。"""
        sig1 = build_content_signature("Hello World", "Content")
        sig2 = build_content_signature("hello world", "content")
        similarity = content_similarity(sig1, sig2)
        assert similarity == 1.0


class TestFindSimilarSignature:
    """测试相似签名查找函数。"""

    def test_no_duplicates(self):
        """测试无重复时返回 None。"""
        candidate = build_content_signature("新标题", "新内容")
        existing = [
            build_content_signature("标题 1", "内容 1"),
            build_content_signature("标题 2", "内容 2"),
        ]
        result = find_similar_signature(candidate, existing, threshold=0.8)
        assert result is None

    def test_exact_duplicate_found(self):
        """测试精确重复被检测到。"""
        candidate = build_content_signature("相同标题", "相同内容")
        existing = [
            build_content_signature("相同标题", "相同内容"),
        ]
        result = find_similar_signature(candidate, existing, threshold=0.8)
        assert result is not None
        assert result["similarity"] == 1.0

    def test_threshold_respected(self):
        """测试阈值被正确应用。"""
        candidate = build_content_signature("相似标题", "相似内容")
        existing = [
            build_content_signature("相似标题", "不同内容"),  # 相似度应该较低
        ]
        
        # 低阈值时应该找到
        result_low = find_similar_signature(candidate, existing, threshold=0.3)
        assert result_low is not None
        
        # 高阈值时应该找不到
        result_high = find_similar_signature(candidate, existing, threshold=0.9)
        assert result_high is None

    def test_returns_highest_similarity(self):
        """测试返回最高相似度的匹配。"""
        candidate = build_content_signature("测试标题", "测试内容")
        existing = [
            build_content_signature("完全不同", "完全不同"),
            build_content_signature("测试标题", "测试内容"),  # 完全匹配
            build_content_signature("部分相似", "部分相似"),
        ]
        result = find_similar_signature(candidate, existing, threshold=0.5)
        assert result is not None
        assert result["similarity"] == 1.0

    def test_empty_existing_list(self):
        """测试空列表时返回 None。"""
        candidate = build_content_signature("标题", "内容")
        result = find_similar_signature(candidate, [], threshold=0.8)
        assert result is None

    def test_similarity_info_included(self):
        """测试结果包含相似度信息。"""
        candidate = build_content_signature("标题", "内容")
        existing = [build_content_signature("标题", "内容")]
        result = find_similar_signature(candidate, existing, threshold=0.5)
        assert "similarity" in result
        assert "matched_title" in result
        assert "matched_preview" in result


class TestDedupWorkflow:
    """测试完整的去重工作流。"""

    def test_generate_unique_signatures(self):
        """测试生成唯一签名。"""
        signatures = []
        test_cases = [
            ("标题 1", "内容 1"),
            ("标题 2", "内容 2"),
            ("标题 3", "内容 3"),
        ]
        
        for title, content in test_cases:
            sig = build_content_signature(title, content)
            duplicate = find_similar_signature(sig, signatures, threshold=0.8)
            assert duplicate is None, f"意外检测到重复：{duplicate}"
            signatures.append(sig)
        
        assert len(signatures) == len(test_cases)

    def test_detect_near_duplicate(self):
        """测试检测近似重复。"""
        signatures = []
        
        # 添加原始内容
        sig1 = build_content_signature("千岛湖亲子酒店攻略", "这是关于千岛湖的详细内容...")
        signatures.append(sig1)
        
        # 尝试添加略微修改的版本
        sig2 = build_content_signature("千岛湖亲子酒店攻略", "这是关于千岛湖的详细内容！")
        duplicate = find_similar_signature(sig2, signatures, threshold=0.85)
        
        # 应该检测到重复（只有标点符号不同）
        assert duplicate is not None
        assert duplicate["similarity"] > 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
