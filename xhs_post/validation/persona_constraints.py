from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from xhs_post.matching import load_persona_config


class PersonaConstraintService:
    def __init__(self, config_dir: str | None = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).resolve().parents[2] / "config"
        self.formality_keywords = {
            "formal": ["您好", "敬请", "谨此", "感谢", "希望", "建议", "请"],
            "semi-formal": ["好呀", "分享", "推荐", "可以", "试试", "一起"],
            "casual": ["家人们", "兄弟们", "绝绝子", "yyds", "种草", "拔草", "冲"],
        }
        self.sentence_length_standards = {
            "low": {"min": 15, "max": 40, "avg": 25},
            "medium": {"min": 10, "max": 30, "avg": 20},
            "high": {"min": 5, "max": 20, "avg": 12},
        }

    def load_persona(self, persona_file: str) -> dict[str, Any]:
        return load_persona_config(self.config_dir, persona_file)

    def check_forbidden_words(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        forbidden_words = persona_config.get("persona", {}).get("forbidden_words", [])
        found_words = [word for word in forbidden_words if word.lower() in content.lower()]
        return {
            "check_type": "forbidden_words",
            "passed": not found_words,
            "found_words": found_words,
            "forbidden_words": forbidden_words,
            "score": 1.0 if not found_words else max(0, 1.0 - len(found_words) * 0.2),
        }

    def check_emoji_density(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        tone = persona_config.get("persona", {}).get("tone", {})
        expected_density = tone.get("emoji_density", 0.3)
        emojis = re.findall(r"[\U00010000-\U0010ffff]", content)
        sentences = [sentence for sentence in re.split(r"[.!?。！？\n]+", content) if sentence.strip()]
        actual_density = len(emojis) / max(len(sentences), 1)
        deviation = abs(actual_density - expected_density)
        return {
            "check_type": "emoji_density",
            "passed": deviation <= 0.3,
            "expected_density": expected_density,
            "actual_density": round(actual_density, 2),
            "deviation": round(deviation, 2),
            "score": round(max(0, 1.0 - deviation), 2),
        }

    def check_sentence_length(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        tone = persona_config.get("persona", {}).get("tone", {})
        standard = self.sentence_length_standards.get(tone.get("energy_level", "medium"), self.sentence_length_standards["medium"])
        sentences = [sentence for sentence in re.split(r"[.!?。！？\n]+", content) if sentence.strip()]
        if not sentences:
            return {"check_type": "sentence_length", "passed": True, "score": 1.0, "expected_range": standard, "actual_avg": 0}
        lengths = [len(sentence) for sentence in sentences]
        avg_length = sum(lengths) / len(lengths)
        in_range = standard["min"] <= avg_length <= standard["max"]
        if in_range:
            score = 1.0
        elif avg_length < standard["min"]:
            score = max(0, 1.0 - (standard["min"] - avg_length) / standard["avg"])
        else:
            score = max(0, 1.0 - (avg_length - standard["max"]) / standard["avg"])
        return {
            "check_type": "sentence_length",
            "passed": in_range,
            "expected_range": standard,
            "actual_avg": round(avg_length, 2),
            "score": round(score, 2),
        }

    def check_formality_level(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        expected_formality = persona_config.get("persona", {}).get("tone", {}).get("formality", "semi-formal")
        scores = {
            level: sum(1 for keyword in keywords if keyword in content)
            for level, keywords in self.formality_keywords.items()
        }
        detected_formality = max(scores, key=scores.get) if any(scores.values()) else "semi-formal"
        passed = detected_formality == expected_formality
        return {
            "check_type": "formality_level",
            "passed": passed,
            "expected_formality": expected_formality,
            "detected_formality": detected_formality,
            "score": 1.0 if passed else 0.6,
        }

    def check_content_domain_relevance(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        domains = persona_config.get("persona", {}).get("content_domains", {})
        all_domains = domains.get("primary", []) + domains.get("secondary", [])
        matched_domains = [domain for domain in all_domains if domain and domain in content]
        score = min(len(matched_domains) / max(len(all_domains), 1), 1.0)
        return {
            "check_type": "content_domain_relevance",
            "passed": bool(matched_domains),
            "matched_domains": matched_domains,
            "all_domains": all_domains,
            "relevance_score": round(score, 2),
            "score": round(score, 2),
        }

    def check_content(self, content: str, persona_config: dict[str, Any]) -> dict[str, Any]:
        checks = {
            "forbidden_words": self.check_forbidden_words(content, persona_config),
            "emoji_density": self.check_emoji_density(content, persona_config),
            "sentence_length": self.check_sentence_length(content, persona_config),
            "formality_level": self.check_formality_level(content, persona_config),
            "content_domain": self.check_content_domain_relevance(content, persona_config),
        }
        overall_score = round(sum(check["score"] for check in checks.values()) / len(checks), 2)
        passed = checks["forbidden_words"]["passed"] and checks["content_domain"]["passed"]
        suggestions = []
        if not checks["forbidden_words"]["passed"]:
            suggestions.append(f"⚠️  移除禁用词：{', '.join(checks['forbidden_words']['found_words'])}")
        if not checks["content_domain"]["passed"]:
            suggestions.append("💡 增强内容与人设领域的相关性")
        if not checks["emoji_density"]["passed"]:
            suggestions.append("💡 调整表情符号密度")
        if not checks["sentence_length"]["passed"]:
            suggestions.append("💡 调整句子长度")
        if not checks["formality_level"]["passed"]:
            suggestions.append("💡 调整语调风格")
        return {
            "passed": passed,
            "overall_score": overall_score,
            "checks": checks,
            "suggestions": suggestions,
        }

    def optimize_content(self, content: str, persona_config: dict[str, Any], max_iterations: int = 3) -> dict[str, Any]:
        history = []
        current_content = content
        for iteration in range(max_iterations):
            result = self.check_content(current_content, persona_config)
            history.append(
                {
                    "iteration": iteration + 1,
                    "content_preview": current_content[:100],
                    "score": result["overall_score"],
                    "passed": result["passed"],
                    "suggestions": result["suggestions"],
                }
            )
            if result["passed"]:
                break
            current_content = content
        return {
            "original_content": content,
            "final_content": current_content,
            "iterations": len(history),
            "history": history,
            "final_passed": history[-1]["passed"] if history else False,
            "final_score": history[-1]["score"] if history else 0,
        }
