#!/usr/bin/env python3
"""
03_generate_posts.py - 生成小红书笔记（通用主题驱动模式）

输入:
  - config/trending_analysis.json (热门分析 - 主题相关)
  - config/generation_state.json (去重状态)
  - xhs_post_from_search/jsonl/*.jsonl (原始数据 - 用于特征提取)

输出:
  - generated_posts/YYYY-MM-DD/post_001.md ~ post_XXX.md

用法:
  # 分析热点数据 (支持主题筛选)
  python scripts/02_analyze_trending.py --topic "主题关键词"

  # 生成笔记 (主题驱动，图片可选)
  python scripts/03_generate_posts.py --topic "主题关键词" --count 10 --use-images optional

  # 一键执行
  bash scripts/run_daily_pipeline.sh "主题关键词"

示例:
  python scripts/02_analyze_trending.py --topic "千岛湖骑行"
  python scripts/03_generate_posts.py --topic "千岛湖骑行" --count 10
  python scripts/03_generate_posts.py --topic "北京美食探店" --count 15
"""

import random
import argparse
from pathlib import Path
from datetime import datetime
import hashlib
import re

from _project_paths import ensure_project_root_on_path, resolve_base_dir

ensure_project_root_on_path()

from xhs_post.storage import load_json, load_jsonl_files, save_json
from xhs_post.images import load_image_analysis, select_images_for_post
from xhs_post.topic import (
    expand_keywords,
    filter_posts_by_source_keyword,
    filter_posts_by_topic,
    parse_like_count,
)

# 配置路径
BASE_DIR = resolve_base_dir()
INPUT_DIR = BASE_DIR / "xhs_post_from_search" / "jsonl"
TRENDING_ANALYSIS_FILE = BASE_DIR / "config" / "trending_analysis.json"
STATE_FILE = BASE_DIR / "config" / "generation_state.json"
IMAGE_ANALYSIS_FILE = BASE_DIR / "config" / "image_analysis.json"
OUTPUT_DIR = BASE_DIR / "generated_posts"

# 爆款标题公式 - 通用版
TITLE_TEMPLATES = {
    "numeric": [
        "我靠这个方法，{time}天{result}",
        "{num}{thing}，让你的{goal}",
        "花了{money}元，换来的{lesson}",
        "{num}年经验分享：{topic}",
        "从{num1}到{num2}，我只做了{num3}件事"
    ],
    "contrast": [
        "别再{old_way}了，试试这个{new_way}",
        "从{state1}到{state2}，我做对了{thing}",
        "{old_result}vs{new_result}，差距在哪？",
        "以前{old_behavior}，现在{new_behavior}",
        "同样的{topic}，为什么{contrast_result}"
    ],
    "pain_point": [
        "还在为{problem}发愁？这个方法绝了",
        "{target_audience}必看！解决你的{pain}",
        "{problem}困扰你很久了？试试这个",
        "谁懂啊！{pain}的痛只有{target}知道",
        "终于找到解决{problem}的办法了"
    ],
    "curiosity": [
        "震惊！原来{topic}还可以这样{action}",
        "{percent}%的人都不知道的{topic}技巧",
        "没想到{topic}居然这么{surprising}",
        "揭秘：{hidden_truth}",
        "不小心发现了{topic}的秘密"
    ],
    "value": [
        "免费分享！价值{value}的{resource}",
        "手把手教你{skill}，建议收藏",
        "纯干货！{topic}看这一篇就够了",
        "超详细{topic}攻略，建议马住",
        "答应我，一定要看完这篇{topic}"
    ]
}

# 通用内容结构模板
CONTENT_STRUCTURE = {
    "pain_intro_templates": [
        "你是不是也和我一样，{pain}...",
        "作为一个{role}，每次{scenario}最头疼的就是{problem}...",
        "{question}...",
        "说实话，{topic}这件事，真正做好的屈指可数...",
        "我相信很多人都有同感：{pain_point}..."
    ],
    "solution_templates": [
        "直到我发现了{solution}，彻底{benefit}！",
        "今天分享的{topic}，真的是{praise}！",
        "我亲测了这个方法，必须安利给大家！",
        "通过这次的体验，我终于找到了理想的{topic}！",
        "亲测！这个{topic}真的能{benefit}..."
    ],
    "core_value_intros": [
        "这家的特别之处：",
        "为什么这个这么值得推荐？因为：",
        "让我来告诉你这个的独特魅力：",
        "这个的亮点真的太多了：",
        "这就是它成为首选的原因：",
        "核心亮点看这里：",
        "最值得体验的部分："
    ],
    "scenes_intros": [
        "特别适合这些场景：",
        "这些时候一定要选这个：",
        "我一般在这些场景下会选择：",
        "推荐给以下人群：",
        "最佳使用场景：",
        "适用情况："
    ],
    "cta_templates": [
        "赶紧收藏吧！评论区告诉我你最喜欢哪个～",
        "觉得有用记得点赞分享哦！",
        "有问题欢迎在评论区留言交流！",
        "关注我，分享更多{topic}干货！",
        "建议马住慢慢看，planning 下一次体验！",
        "收藏起来，下次就用得上！",
        "欢迎评论区分享你的经验～"
    ]
}

def extract_topic_features(topic: str, raw_posts: list) -> dict:
    """从原始数据中提取主题特征"""
    # 1. 关键词扩展 + 筛选
    keywords = expand_keywords(topic)
    related_posts = filter_posts_by_topic(raw_posts, keywords)

    if not related_posts:
        print(f"⚠️  未找到与主题 '{topic}' 相关的内容")
        return {}

    # 2. 获取高赞内容 (Top 20)
    top_posts = sorted(related_posts,
                       key=lambda x: parse_like_count(x.get("liked_count", "0")),
                       reverse=True)[:20]

    # 3. 提取标签
    def extract_tags_from_posts(posts):
        tags = []
        for post in posts:
            tag_list = post.get('tag_list', '')
            if tag_list:
                tags.extend([t.strip() for t in tag_list.split(',')])
        return list(set(tags))

    # 4. 提取价值点
    def extract_value_points(posts):
        value_points = []
        value_keywords = ['特别', '亮点', '特色', '值得', '推荐', '喜欢', '满意', '惊喜', '棒', '绝', '赞']

        for post in posts:
            desc = post.get('desc', '')
            if not desc:
                continue

            sentences = re.split(r'[,.!?.\n]', desc)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and any(kw in sentence for kw in value_keywords):
                    if sentence not in value_points:
                        value_points.append(sentence)

        return value_points[:50]

    # 5. 提取场景
    def extract_scenes(posts):
        scenes = []
        scene_keywords = ['适合', '推荐', '场景', '时候', '人群', '情况', '最佳']

        for post in posts:
            desc = post.get('desc', '')
            if not desc:
                continue

            sentences = re.split(r'[,.!?.\n]', desc)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 5 and any(kw in sentence for kw in scene_keywords):
                    if sentence not in scenes:
                        scenes.append(sentence)

        return scenes[:30]

    # 6. 提取痛点
    def extract_pain_points(posts):
        pain_points = []
        pain_keywords = ['头疼', '困扰', '烦恼', '担心', '害怕', '最怕', '问题', '难点', '坑', '雷', '愁']

        for post in posts:
            desc = post.get('desc', '')
            if not desc:
                continue

            sentences = re.split(r'[,.!?.\n]', desc)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 5 and any(kw in sentence for kw in pain_keywords):
                    if sentence not in pain_points:
                        pain_points.append(sentence)

        return pain_points[:30]

    # 3. 提取特征
    features = {
        "titles": [p["title"] for p in top_posts if p.get("title")],
        "descriptions": [p["desc"] for p in top_posts if p.get("desc")],
        "tags": extract_tags_from_posts(top_posts),
        "value_points": extract_value_points(top_posts),
        "scenes": extract_scenes(top_posts),
        "audiences": [],  # 从内容中提取较难，暂时留空
        "pain_points": extract_pain_points(top_posts),
    }

    return features


def get_general_tags_for_topic(topic: str) -> list:
    """根据主题类型返回通用流量标签"""
    if "亲子" in topic or "带娃" in topic or "遛娃" in topic:
        return ["#亲子游", "#带娃旅行", "#遛娃好去处", "#亲子时光", "#宝妈分享"]
    elif "骑行" in topic or "户外" in topic or "徒步" in topic:
        return ["#户外运动", "#骑行", "#周末运动", "#户外生活", "#运动日常"]
    elif "美食" in topic or "餐厅" in topic or "探店" in topic:
        return ["#美食探店", "#吃货", "#本地美食", "#美食推荐", "#吃喝玩乐"]
    elif "酒店" in topic or "住宿" in topic or "民宿" in topic:
        return ["#酒店推荐", "#度假", "#旅行住宿", "#宝藏酒店", "#住宿推荐"]
    elif "旅游" in topic or "旅行" in topic or "攻略" in topic:
        return ["#旅行攻略", "#旅游攻略", "#周末去哪儿", "#小众旅游", "#旅行日记"]
    elif "摄影" in topic or "拍照" in topic:
        return ["#摄影日常", "#拍照技巧", "#约拍", "#摄影作品", "#拍照打卡"]
    else:
        return ["#周末去哪儿", "#小众旅游", "#旅行攻略", "#生活记录", "#日常分享"]


def generate_titles_for_topic(topic: str, features: dict, count: int = 5, topic_keywords: list = None) -> list:
    """为主题生成爆款标题"""
    titles = []
    topic_words = topic.split()

    # 检查标题是否与主题相关
    def is_title_relevant(title: str, keywords: list) -> bool:
        if not keywords or not title:
            return True
        title_lower = title.lower()

        # 首先检查是否包含明显不相关的知名地名/事物
        unrelated_places = ['西双版纳', '北京', '上海', '云南', '泰国', '日本', '欧洲']
        for place in unrelated_places:
            if place in title and place not in topic_words:
                return False

        # 检查是否包含主题关键词
        for kw in keywords:
            if kw in title_lower:
                return True

        # 检查是否是通用标题模式（不包含具体地名/事物名）
        # 通用标题通常包含方法论词汇而不是具体地名
        generic_patterns = ['怎么', '如何', '方法', '技巧', '经验', '分享']
        has_generic = any(p in title for p in generic_patterns)

        # 如果标题有具体地名但不是主题地名，则不相关
        has_specific_place = False
        for word in title.split():
            if len(word) >= 3 and word in unrelated_places:
                has_specific_place = True
                break

        if has_specific_place:
            return False

        # 如果是通用模式且没有不相关地名，可以接受
        if has_generic:
            return True

        return False

    # 尝试从特征中提取标题模式
    if features.get("titles"):
        # 从高赞标题中随机选择与主题相关的
        for title in features["titles"]:
            if is_title_relevant(title, topic_keywords):
                # 限制标题长度（小红书建议 20 字以内，最多 30 字）
                if title not in titles and 5 <= len(title) <= 30:
                    titles.append(title)
                    if len(titles) >= count:
                        break

    # 如果不够，使用模板生成
    while len(titles) < count:
        template_type = random.choice(list(TITLE_TEMPLATES.keys()))
        template = random.choice(TITLE_TEMPLATES[template_type])

        # 主题词
        main_topic = topic
        sub_topic = topic.split()[-1] if len(topic.split()) > 1 else topic

        # 简单替换主题词
        title = template
        title = title.replace("{topic}", main_topic)
        title = title.replace("{thing}", sub_topic)
        title = title.replace("{skill}", sub_topic)
        title = title.replace("{result}", "轻松搞定" if "酒店" in main_topic or "住宿" in main_topic else "完美解决")
        title = title.replace("{goal}", "体验升级")
        title = title.replace("{lesson}", "的宝贵经验")
        title = title.replace("{time}", str(random.randint(1, 7)))
        title = title.replace("{num}", str(random.randint(3, 10)))
        title = title.replace("{num1}", str(random.randint(1, 5)))
        title = title.replace("{num2}", str(random.randint(6, 10)))
        title = title.replace("{num3}", str(random.randint(1, 3)))
        title = title.replace("{money}", str(random.randint(100, 5000)))
        title = title.replace("{percent}", str(random.randint(80, 99)))
        title = title.replace("{value}", str(random.randint(1000, 10000)))
        title = title.replace("{resource}", "攻略")
        title = title.replace("{old_way}", "盲目选择")
        title = title.replace("{new_way}", "这篇攻略")
        title = title.replace("{state1}", "选择困难")
        title = title.replace("{state2}", "轻松决定")
        title = title.replace("{old_result}", "踩雷")
        title = title.replace("{new_result}", "满意")
        title = title.replace("{old_behavior}", "随便订房")
        title = title.replace("{new_behavior}", "看攻略再选")
        title = title.replace("{contrast_result}", "别人踩雷你满意")
        title = title.replace("{problem}", "选择")
        title = title.replace("{target_audience}", "旅行爱好者")
        title = title.replace("{pain}", "选择的烦恼")
        title = title.replace("{target}", "过来人")
        title = title.replace("{action}", "玩")
        title = title.replace("{surprising}", "值得")
        title = title.replace("{hidden_truth}", "选择的秘诀")

        # 清理未替换的占位符 - 用合理的默认值替换
        title = re.sub(r'\{[^}]+\}', '', title)
        title = title.strip()

        # 过滤掉过短或过长的标题（小红书标题建议 20 字以内）
        # 过滤掉语法不完整的标题
        if title and 5 <= len(title) <= 30 and title not in titles:
            titles.append(title)

    return titles[:count]


def generate_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """基于提取的特征生成内容（黄金 5 段式）- 实际使用特征数据"""
    return _generate_feature_based_content(topic, features, topic_keywords)

def _generate_feature_based_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """基于提取的特征生成内容（黄金 5 段式）"""
    import random, re
    
    sections = []
    seen_content = set()
    topic_words = topic.split()
    
    related_places = {
        '西双版纳': ['告庄', '星光夜市', '曼听公园', '总佛寺', '野象谷', '植物园', '傣族园', '基诺山', '雨林', '告庄西双景', '景洪', '澜沧江', '大金塔', '江边夜市', '曼远村', '热带雨林谷'],
        '千岛湖': ['天屿山', '千岛湖大桥', '骑龙巷', '啤酒小镇', '灯塔', '东南湖区', '中心湖区', '梅峰岛', '黄山尖', '千岛湖'],
    }
    topic_related = related_places.get(topic, [])
    
    def is_relevant(text):
        if not text or len(text) < 15:
            return False
        for word in topic_words:
            if len(word) > 1 and word in text:
                return True
        for place in topic_related:
            if place in text:
                return True
        if len(text) > 50:
            return True
        return False
    
    def clean_text(text):
        text = re.sub(r'#\w+[话题]#', '', text)
        text = re.sub(r'\[\w+R\]', '', text)
        text = re.sub(r'\d+[️⃣]', '', text)
        return text.strip()
    
    def add_unique(items, max_count=4):
        result = []
        shuffled = items.copy()
        random.shuffle(shuffled)
        for item in shuffled:
            clean = clean_text(item)
            if clean and clean not in seen_content and len(clean) > 20:
                seen_content.add(clean)
                result.append(clean)
                if len(result) >= max_count:
                    break
        return result
    
    relevant_vps = [vp for vp in features.get('value_points', []) if is_relevant(vp)]
    relevant_scenes = [sc for sc in features.get('scenes', []) if is_relevant(sc)]
    relevant_pains = [pp for pp in features.get('pain_points', []) if is_relevant(pp)]
    
    if relevant_pains:
        pains = add_unique(relevant_pains, 1)
        if pains:
            sections.append(pains[0])
    
    if len(sections) == 0:
        sections.append(f"关于{topic}，我有一些真实体验想分享...")
    
    sections.append(f"这次在{topic}的体验，完全超出预期！")
    
    if relevant_vps:
        vps = add_unique(relevant_vps, 4)
        emojis = ["✅", "⭐️", "🎯", "💎", "✨", "🌟"]
        for i, vp in enumerate(vps):
            sections.append(f"{emojis[i % len(emojis)]} {vp}")
    else:
        sections.append(f"✨ {topic}的体验真的很棒")
        sections.append("🎯 细节到位，服务周到")
    
    sections.append("")
    sections.append("推荐在这些时候选择：")
    
    if relevant_scenes:
        scenes = add_unique(relevant_scenes, 3)
        for scene in scenes:
            sections.append(f"• {scene}")
    else:
        sections.append("• 周末短途放松")
        sections.append("• 假期深度体验")
    
    sections.append("")
    sections.append(f"关于{topic}，有问题欢迎评论区留言！")
    
    return "\n\n".join(sections)


def _generate_merchant_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """商家推广内容生成（内部函数）"""
    import random
    
    # 判断主题类型
    topic_lower = topic.lower()
    is_hotel = any(k in topic_lower for k in ["酒店", "民宿", "住宿", "客栈", "公寓"])
    is_family = any(k in topic_lower for k in ["亲子", "带娃", "遛娃", "儿童", "宝宝", "家庭"])
    
    # 5种内容模式
    content_patterns = []
    
    if is_hotel and is_family:
        # 亲子酒店场景
        content_patterns = [
            # 行程型
            """作为一个带孩子的家长，每次出门最担心的就是行程安排太赶孩子闹。
        
这次去千岛湖，我直接选了亲子酒店当大本营，意外地发现这样玩反而更轻松！

【2天1夜懒人路线】
Day1: 到达酒店 -> 儿童活动区/草坪玩耍 -> 午餐休息 -> 下午在酒店周边散步 -> 傍晚看日落
Day2: 酒店早餐 -> 轻松景点游览 -> 午休返程

孩子最喜欢的不是景区，而是酒店里的儿童区和湖边草坪。这种玩法对带娃家庭真的友好太多。""",
            
            # 痛点型
            """带3岁娃去千岛湖，订酒店我只看这5件事：
        
1. 有没有儿童活动区
2. 早餐适不适合小朋友
3. 房间能不能加婴儿床
4. 离主要景点远不远
5. 娃午睡后还能不能继续玩

这次住的这家刚好把这些都覆盖了。特别是儿童活动区，娃能放电，大人能休息，简直是带娃神器。""",
            
            # 对比型
            """千岛湖亲子游，住景区民宿和住亲子酒店差别太大了：

【民宿】折腾程度高 | 孩子配套少 | 天气风险大 | 爸妈休息难
【亲子酒店】一站式服务 | 放电项目多 | 雨天有室内 | 大人也轻松

带娃出行最重要的就是省心，亲子酒店真的更适合低风险旅行。""",
            
            # 情绪价值型
            """千岛湖这个周末，我什么都没抢着玩，只是看着孩子在草地上跑。

没有赶行程，没有催孩子，没有争执。
就是简单地：
孩子在草地跑
看湖
做手工
吃顿不吵架的早餐
爸妈终于坐下来

原来周末的正确打开方式，是找一个让孩子放电、让自己喘息的地方。""",
            
            # 避坑型
            """本来想订民宿，最后还是选了这家亲子酒店。

说下我的考虑：
带娃出行临时状况太多了 - 困了、饿了、闹了、天气变了...
民宿人生地不熟，还是连锁亲子酒店更靠谱：
服务稳定、配套齐全、应对突发能力强

这次住下来，不得不说带娃家庭选这里是对的。"""
        ]
    elif is_hotel:
        content_patterns = [
            """这次去千岛湖选了这家酒店，说下真实体验：

位置便利性：周边景点距离合适，出行方便
设施配套：房间配置齐全，该有的都有
服务体验：工作人员态度好，响应及时

整体来说，是一次不错的住宿体验。""",
            
            """千岛湖旅行住宿怎么选？分享我的经验：

选择这家酒店的主要原因：
1. 位置好，去主要景点都方便
2. 口碑不错，评价很真实
3. 性价比可以，配套对得起价格

住了几天，整体感受超出预期。"""
        ]
    else:
        content_patterns = [
            f"""发现了一个{topic}的好地方，必须分享出来：

去了才知道，真的很值得一来。
具体怎么样呢？往下看~

✨ 亮点分享：
- 体验感很棒
- 适合拍照打卡
- 值得多次打卡

整体来说，是一次不错的体验，推荐！""",
            
            f"""关于{topic}，我有话要说：

去之前做了很多功课，最终选了这里。
实际体验下来，有几点超预期：
1. 氛围感很强
2. 出片率高
3. 服务周到

想去的可以参考~"""
        ]
    
    # 选择内容模式
    selected = random.choice(content_patterns)
    
    return selected
    
    # 统计相关特征数量（去重）
    seen_content = set()  # 用于去重
    
    topic_words = topic.split()
    
    def is_topic_relevant(text: str, keywords: list) -> bool:
        if not text:
            return False
        if not keywords:
            return len(text) > 20  # 没有关键词时，长度>20 的保留
        # 检查是否包含主题词或相关地名
        for word in topic_words:
            if len(word) > 1 and word in text:
                return True
        # 检查长度>50 的句子（通常是高质量内容）
        if len(text) > 50:
            return True
        return False
    
    def add_unique(items: list, max_count: int = 3) -> list:
        """添加不重复的条目（随机选择）"""
        result = []
        # 先打乱顺序，然后选择不重复的
        shuffled = items.copy()
        random.shuffle(shuffled)
        for item in shuffled:
            # 清理内容
            clean_item = item.strip().replace('▫️', '').replace('•', '').strip()
            # 检查是否重复
            if clean_item and clean_item not in seen_content:
                seen_content.add(clean_item)
                result.append(clean_item)
                if len(result) >= max_count:
                    break
        return result
    
    relevant_value_points = []
    relevant_scenes = []
    relevant_pain_points = []
    
    if topic_keywords:
        # 筛选与主题相关的价值点
        for point in features.get("value_points", []):
            if is_topic_relevant(point, topic_keywords):
                relevant_value_points.append(point)
        
        # 筛选与主题相关的场景
        for scene in features.get("scenes", []):
            if is_topic_relevant(scene, topic_keywords):
                relevant_scenes.append(scene)
        
        # 筛选与主题相关的痛点
        for pain in features.get("pain_points", []):
            if is_topic_relevant(pain, topic_keywords):
                relevant_pain_points.append(pain)
    
    # 1. 痛点引入
    if relevant_pain_points:
        unique_pains = add_unique(relevant_pain_points, 1)
        if unique_pains:
            sections.append(unique_pains[0])
    
    if len(sections) == 0:
        # 使用通用模板
        template = "说实话，{topic} 这件事，真正懂的人不多..."
        sections.append(template.replace("{topic}", topic))
    
    # 2. 解决方案引入
    sections.append(f"今天分享的这份{topic}，是我亲测多次后总结的精华！")
    
    # 3. 核心价值 - 仅使用相关的价值点（去重，随机选择）
    if relevant_value_points:
        unique_points = add_unique(relevant_value_points, 4)
        emojis = ["✅", "⭐️", "🎯", "💎", "✨", "🌟", "🚀", "💫"]
        for i, point in enumerate(unique_points):
            emoji = emojis[i % len(emojis)]
            sections.append(f"{emoji} {point}")
    else:
        # 使用通用价值描述
        sections.append(f"✨ {topic}的优质体验")
        sections.append(f"🎯 精心设计的细节和服务")
        sections.append(f"💎 超出预期的满意度")
    
    # 4. 使用场景（去重，随机选择）
    sections.append("")
    sections.append("我一般在这些场景下会选择：")
    
    if relevant_scenes:
        unique_scenes = add_unique(relevant_scenes, 3)
        for scene in unique_scenes:
            sections.append(f"• {scene}")
    else:
        # 通用场景
        if "亲子" in topic or "带娃" in topic:
            sections.append(f"• 周末两天一夜家庭短途游")
            sections.append(f"• 寒暑假亲子长假")
        elif "骑行" in topic or "户外" in topic:
            sections.append(f"• 周末户外运动时光")
            sections.append(f"• 朋友结伴探索")
        elif "美食" in topic:
            sections.append(f"• 周末美食探店之旅")
            sections.append(f"• 与朋友共享美食时光")
        else:
            sections.append(f"• 周末短途体验")
            sections.append(f"• 假期长途旅行")
    
    # 5. 行动号召
    sections.append("")
    sections.append(f"关于{topic}，有问题欢迎评论区留言！")
    
    return "\n\n".join(sections)

    return "\n\n".join(sections)


def generate_tags(topic: str, features: dict, topic_keywords: list = None) -> list:
    """生成 10-15 个与主题相关的标签"""
    tags = []

    topic_words = topic.split()

    # 1. 首先添加通用流量标签（基于主题类型）
    general_tags = get_general_tags_for_topic(topic)
    tags.extend(general_tags)

    # 2. 从热点数据提取标签（仅当与主题相关时）
    hot_tags = features.get("tags", [])
    if topic_keywords:
        for tag in hot_tags[:20]:
            # 检查标签是否与主题相关 - 必须包含主题词之一
            is_relevant = False
            for word in topic_words:
                if len(word) > 1 and word in tag:
                    is_relevant = True
                    break

            if is_relevant:
                if not tag.startswith("#"):
                    tag = f"#{tag}"
                if tag not in tags:
                    tags.append(tag)

    # 3. 添加主题本身的标签
    topic_tags = topic.split()
    for tag_word in topic_tags:
        if len(tag_word) > 1:  # 单字词不添加
            tag = f"#{tag_word}"
            if tag not in tags:
                tags.append(tag)

    # 4. 去重，限制数量
    tags = list(dict.fromkeys(tags))[:15]

    # 确保至少有 8 个标签
    while len(tags) < 8:
        generic_tag = "#生活记录" if "#生活记录" not in tags else "#日常分享"
        if generic_tag not in tags:
            tags.append(generic_tag)
        else:
            break

    return tags

def generate_unique_id(content: str) -> str:
    """生成内容唯一标识"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]


def generate_post(post_id: int, topic: str, trending_data: dict, raw_posts: list,
                  used_titles: list, angle: str = None, image_analyses: list | None = None,
                  used_combinations: list | None = None) -> dict:
    """生成单篇笔记（主题驱动模式）
    
    Args:
        post_id: 笔记序号
        topic: 主题关键词
        trending_data: 热点分析数据
        raw_posts: 原始笔记数据
        used_titles: 已使用的标题列表（去重）
        angle: 笔记角度/卖点（如"必住推荐"、"亲子攻略"、"性价比之选"等）
    """
    print(f"  正在生成第 {post_id} 篇笔记...")

    # 生成与主题相关的角度标签
    if not angle:
        # 随机选择一个笔记角度
        angles = ["必去推荐", "避坑指南", "省钱攻略", "深度体验", "本地人推荐", "小众玩法"]
        angle = random.choice(angles)
    
    # 清理角度名称，用于文件名
    angle_filename = angle.replace(" ", "_").replace("/", "_")[:20]
    topic_filename = topic.replace(" ", "_").replace("/", "_")[:15]
    
    # 构建笔记ID（基于主题和角度）
    post_id_str = f"{topic_filename}_{angle_filename}_{post_id:03d}"

    # 从 trending_data 或原始数据提取特征
    features = trending_data.get("features", {})

    # 如果 trending_data 没有 features，从原始数据提取
    if not features and raw_posts:
        features = extract_topic_features(topic, raw_posts)

    # 获取主题关键词（用于内容相关性过滤）
    topic_keywords = expand_keywords(topic)

    # 生成标题（确保不重复，且与主题相关）
    max_attempts = 20
    for attempt in range(max_attempts):
        titles = generate_titles_for_topic(topic, features, count=random.randint(3, 5), topic_keywords=topic_keywords)
        if not any(t in used_titles for t in titles):
            break
    else:
        titles = generate_titles_for_topic(topic, features, count=5, topic_keywords=topic_keywords)

    used_titles.extend(titles)

    # 生成内容（传入主题关键词用于过滤）
    content = generate_content(topic, features, topic_keywords)

    # 生成标签（传入关键词用于过滤）
    tags = generate_tags(topic, features, topic_keywords)

    # 选择发布时间
    posting_times = trending_data.get('recommended_posting_times', [
        "早上 8:00", "中午 12:30", "晚上 19:00", "晚上 21:30"
    ])
    best_time = random.choice(posting_times) if posting_times else "早上 8:00"

    # 构建笔记（使用主题相关的ID）
    post = {
        "id": post_id_str,  # 格式: topic_angle_001
        "titles": titles,
        "tags": tags,
        "content": content,
        "best_posting_time": best_time,
        "created_at": datetime.now().isoformat(),
        "content_id": generate_unique_id(content),
        "topic": topic,
        "angle": angle,  # 记录笔记角度
    }

    selected_images, combination_id = select_images_for_post(
        topic=topic,
        angle=angle,
        image_analyses=image_analyses or [],
        used_combinations=used_combinations or [],
    )
    post["images"] = selected_images
    post["image_combination_id"] = combination_id

    return post


def format_post_markdown(post: dict) -> str:
    """将笔记格式化为 Markdown"""
    md = []

    # 标题
    md.append(f"# 🔥 标题选项 ({len(post['titles'])} 个)")
    for i, title in enumerate(post['titles'], 1):
        md.append(f"{i}. {title}")

    md.append("")

    # 标签
    md.append("## 🏷️ 推荐标签")
    md.append(" ".join(post['tags']))

    md.append("")

    md.append("## 📸 配图")
    if post.get("images"):
        for index, image in enumerate(post["images"], 1):
            md.append(f"{index}. [{image['role']}] {image['path']} ({image.get('theme', '未标注')})")
    else:
        md.append("⚠️ 暂无可用图片，请先运行图片分析 workflow")

    md.append("")

    # 正文
    md.append("## ✍️ 正文")
    md.append("")
    md.append(post['content'])

    md.append("")

    # 发布时间
    md.append("## ⏰ 最佳发布时间")
    md.append(post['best_posting_time'])

    md.append("")
    md.append("---")
    md.append(f"*生成时间：{post['created_at']}*")
    md.append(f"*内容 ID: {post['content_id']}*")
    md.append(f"*主题：{post.get('topic', '未指定')}*")

    return "\n".join(md)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='小红书笔记生成器 - 通用主题驱动模式')
    parser.add_argument('--topic', type=str, required=True,
                        help='生成笔记的主题（必填）')
    parser.add_argument('--count', type=int, default=10,
                        help='生成笔记数量（默认：10）')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='输出目录（默认：~/XHS_Post/generated_posts/YYYY-MM-DD/）')
    parser.add_argument('--input', type=str, default=None,
                        help='热点分析结果路径（默认：config/trending_analysis.json）')
    parser.add_argument('--strict', action='store_true',
                        help='严格模式：无相关数据时报错退出（默认启用）')
    parser.add_argument('--seed', type=int, default=None,
                        help='随机种子（用于测试和复现）')

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # 设置输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_dir = OUTPUT_DIR / today
    trending_analysis_file = Path(args.input) if args.input else TRENDING_ANALYSIS_FILE

    print("=" * 60)
    print("📝 小红书笔记生成器 - 通用主题驱动模式")
    print("=" * 60)
    print(f"\n🎯 生成主题：{args.topic}")
    print(f"📊 生成数量：{args.count} 篇")
    print(f"📂 输出目录：{output_dir}")

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 加载数据
    print("\n📂 加载数据...")
    trending_data = load_json(trending_analysis_file)
    state_data = load_json(STATE_FILE)
    image_analyses = load_image_analysis(IMAGE_ANALYSIS_FILE)

    # 检查分析数据是否存在且与主题匹配
    if not trending_data:
        print("❌ 错误：未找到热点分析数据")
        print(f"   请先运行：python scripts/02_analyze_trending.py --topic '{args.topic}'")
        return

    if trending_data.get("topic") != args.topic:
        print(f"❌ 错误：分析数据主题不匹配")
        print(f"   当前分析数据主题：'{trending_data.get('topic')}'")
        print(f"   请求生成主题：'{args.topic}'")
        print(f"\n💡 解决方案：")
        print(f"   1. 重新运行分析：python scripts/02_analyze_trending.py --topic '{args.topic}'")
        print(f"   2. 或使用 --topic '{trending_data.get('topic')}' 生成现有主题的笔记")
        return

    # 检查是否有足够的相关数据
    high_performing = trending_data.get("high_performing_posts", 0)
    total_analyzed = trending_data.get("total_posts_analyzed", 0)

    if total_analyzed == 0:
        print(f"❌ 错误：没有找到与 '{args.topic}' 相关的笔记数据")
        print(f"\n💡 解决方案：")
        print(f"   1. 确认数据文件 xhs_post_from_search/jsonl/*.jsonl 中存在 source_keyword='{args.topic}' 的数据")
        print(f"   2. 或者使用爬虫重新抓取 '{args.topic}' 主题的数据")
        print(f"   3. 检查 02_analyze_trending.py 是否正确运行")
        return

    if high_performing == 0:
        print(f"⚠️  警告：找到 {total_analyzed} 篇相关笔记，但没有高赞笔记（点赞>3000）")
        print(f"   将使用所有相关笔记进行分析...")
    else:
        print(f"✅ 数据检查通过：{total_analyzed} 篇相关笔记，{high_performing} 篇高赞笔记")

    # 加载原始数据（用于特征提取）
    raw_posts = []
    if INPUT_DIR.exists():
        print(f"\n  加载原始数据：{INPUT_DIR}/*.jsonl")
        raw_posts = load_jsonl_files(INPUT_DIR)

        # 按 source_keyword 过滤原始数据
        raw_posts = filter_posts_by_source_keyword(raw_posts, args.topic)
        print(f"  • 原始笔记总数：{len(raw_posts)} 篇（已按主题相关性过滤）")

    used_combinations = state_data.get('used_combinations', [])
    print(f"  • 已用组合：{len(used_combinations)} 个")
    print(f"  • 可用图片：{len(image_analyses)} 张")

    # 生成笔记
    print(f"\n🎨 开始生成 {args.count} 篇笔记...")
    posts = []
    used_titles = []

    for i in range(1, args.count + 1):
        post = generate_post(
            i,
            args.topic,
            trending_data,
            raw_posts,
            used_titles,
            image_analyses=image_analyses,
            used_combinations=used_combinations,
        )
        posts.append(post)
        if post.get("image_combination_id"):
            used_combinations.append(post["image_combination_id"])

        # 保存单篇笔记
        output_file = output_dir / f"{post['id']}.md"
        markdown_content = format_post_markdown(post)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"  ✅ {post['id']}: {output_file.name}")

    # 更新状态
    current_date = datetime.now().strftime("%Y-%m-%d")
    state_data['used_combinations'] = used_combinations
    state_data['last_run'] = datetime.now().isoformat()
    state_data['total_posts_generated'] += len(posts)
    state_data['last_generation'] = {
        "topic": args.topic,
        "count": len(posts),
        "date": current_date,
        "post_ids": [p['id'] for p in posts]
    }
    state_data['daily_history'].append({
        "date": current_date,
        "posts_generated": len(posts),
        "post_ids": [p['id'] for p in posts],
        "topic": args.topic
    })

    save_json(STATE_FILE, state_data)

    # 总结
    print(f"\n{'=' * 60}")
    print("✅ 笔记生成完成！")
    print(f"\n📊 生成统计:")
    print(f"  • 生成笔记：{len(posts)} 篇")
    print(f"  • 主题：{args.topic}")
    print(f"  • 输出目录：{output_dir}")
    print(f"  • 累计生成：{state_data['total_posts_generated']} 篇")

    print(f"\n📝 文件列表:")
    for post in posts:
        print(f"  • {post['id']}.md - {' '.join(post['tags'][:3])}...")

    print(f"\n💾 分析输入：{trending_analysis_file}")
    print(f"💾 状态已更新：{STATE_FILE}")
    print(f"{'=' * 60}")

    return posts


if __name__ == "__main__":
    main()

def generate_post_angle(topic: str, trending_data: dict = None) -> str:
    """根据主题和热点数据生成笔记角度/卖点
    
    从热点分析中提取热门角度，生成与主题相关的笔记卖点
    """
    import random
    
    # 通用角度模板
    common_angles = [
        "必住推荐", "保姆级攻略", "避坑指南", "实测体验", 
        "宝藏民宿", "网红打卡", "亲子友好", "性价比之选",
        "绝绝子", "实用分享", "强烈推荐", "必看攻略"
    ]
    
    # 根据主题类型匹配角度
    topic_lower = topic.lower()
    
    # 酒店/民宿相关
    if any(k in topic_lower for k in ["酒店", "民宿", "住宿", "客栈", "公寓"]):
        hotel_angles = [
            "酒店测评", "住宿推荐", "入住体验", "房间揭秘",
            "服务点评", "早餐评测", "设施盘点", "周边攻略"
        ]
        common_angles.extend(hotel_angles)
    
    # 美食相关
    if any(k in topic_lower for k in ["美食", "餐厅", "小吃", "探店", "吃喝"]):
        food_angles = [
            "美食测评", "探店打卡", "必吃清单", "隐藏菜单",
            "口味评测", "性价比", "排队也要吃", "本地人推荐"
        ]
        common_angles.extend(food_angles)
    
    # 旅游/攻略相关
    if any(k in topic_lower for k in ["旅游", "攻略", "游玩", "旅行", "出行"]):
        travel_angles = [
            "保姆级攻略", "行程规划", "打卡指南", "必玩项目",
            "小众景点", "旅行干货", "避坑攻略", "实用tips"
        ]
        common_angles.extend(travel_angles)
    
    # 亲子相关
    if any(k in topic_lower for k in ["亲子", "带娃", "遛娃", "儿童", "宝宝"]):
        family_angles = [
            "亲子攻略", "遛娃圣地", "儿童友好", "宝宝必备",
            "亲子活动", "度假推荐", "全家满意"
        ]
        common_angles.extend(family_angles)
    
    # 从热点数据中提取热门标签作为角度参考
    if trending_data and trending_data.get("trending_tags"):
        trending_tags = trending_data.get("trending_tags", [])
        if trending_tags:
            # 取前5个热门标签，生成角度
            for tag in trending_tags[:5]:
                tag_name = tag.get("name", "").replace("#", "")
                if tag_name:
                    angle_from_tag = f"#{tag_name}"
                    if angle_from_tag not in common_angles:
                        common_angles.append(angle_from_tag)
    
    # 随机选择一个角度
    return random.choice(common_angles)

def generate_merchant_focused_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """生成商家推广角度的内容（改进版）
    
    核心思路：
    1. 不要直接卖酒店，要卖"亲子度假场景"
    2. 家长买的不是住宿，而是：孩子有得玩、爸妈不累、行程省心、拍照好看
    3. 酒店是行程的"起点"和"枢纽"
    """
    import random
    
    # 判断主题类型
    topic_lower = topic.lower()
    is_hotel = any(k in topic_lower for k in ["酒店", "民宿", "住宿", "客栈", "公寓"])
    is_family = any(k in topic_lower for k in ["亲子", "带娃", "遛娃", "儿童", "宝宝", "家庭"])
    
    # 内容模板 - 根据主题类型选择
    if is_hotel and is_family:
        # 亲子酒店场景 - 重点方向
        return generate_family_hotel_content(topic, features, topic_keywords)
    elif is_hotel:
        # 普通酒店场景
        return generate_hotel_content(topic, features, topic_keywords)
    else:
        # 通用场景
        return generate_general_content(topic, features, topic_keywords)


def generate_family_hotel_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """生成亲子酒店场景内容"""
    import random
    
    # 5种内容模式（按照用户提供的框架）
    content_patterns = [
        # 行程型
        """作为一个带孩子的家长，每次出门最担心的就是行程安排太赶孩子闹。
        
这次去千岛湖，我直接选了亲子酒店当大本营，意外地发现这样玩反而更轻松！

【2天1夜懒人路线】
Day1: 到达酒店 -> 儿童活动区/草坪玩耍 -> 午餐休息 -> 下午在酒店周边散步 -> 傍晚看日落
Day2: 酒店早餐 -> 轻松景点游览 -> 午休返程

孩子最喜欢的不是景区，而是酒店里的儿童区和湖边草坪。这种玩法对带娃家庭真的友好太多。""",
        
        # 痛点型
        """带3岁娃去千岛湖，订酒店我只看这5件事：
        
1. 有没有儿童活动区
2. 早餐适不适合小朋友
3. 房间能不能加婴儿床
4. 离主要景点远不远
5. 娃午睡后还能不能继续玩

这次住的这家刚好把这些都覆盖了。特别是儿童活动区，娃能放电，大人能休息，简直是带娃神器。""",
        
        # 对比型
        """千岛湖亲子游，住景区民宿和住亲子酒店差别太大了：

【民宿】折腾程度高 ⭐⭐⭐ | 孩子配套少 ⭐ | 天气风险大 ⭐ | 爸妈休息难 ⭐
【亲子酒店】一站式服务 ⭐⭐⭐⭐ | 放电项目多 ⭐⭐⭐⭐ | 雨天有室内 ⭐⭐⭐⭐ | 大人也轻松 ⭐⭐⭐⭐

带娃出行最重要的就是省心，亲子酒店真的更适合低风险旅行。""",
        
        # 情绪价值型
        """千岛湖这个周末，我什么都没抢着玩，只是看着孩子在草地上跑。

没有赶行程，没有催孩子，没有争执。
就是简单地：
孩子在草地跑
看湖
做手工
吃顿不吵架的早餐
爸妈终于坐下来

原来周末的正确打开方式，是找一个让孩子放电、让自己喘息的地方。""",
        
        # 避坑型
        """本来想订民宿，最后还是选了这家亲子酒店。

说下我的考虑：
带娃出行临时状况太多了 - 困了、饿了、闹了、天气变了...
民宿人生地不熟，还是连锁亲子酒店更靠谱：
服务稳定、配套齐全、应对突发能力强

这次住下来，不得不说带娃家庭选这里是对的。"""
    ]
    
    # 选择一个模式，或者组合多个
    selected = random.sample(content_patterns, min(2, len(content_patterns)))
    
    # 添加产品相关描述
    product_desc = generate_product_embedding(topic, features)
    
    # 组合内容
    content = "\n\n---\n\n".join(selected)
    content += f"\n\n{product_desc}"
    
    return content


def generate_hotel_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """生成普通酒店场景内容"""
    import random
    
    templates = [
        """这次去千岛湖选了这家酒店，说下真实体验：

位置便利性：
周边景点距离合适，出行方便

设施配套：
房间配置齐全，该有的都有

服务体验：
工作人员态度好，响应及时

整体来说，是一次不错的住宿体验。""",
        
        """千岛湖旅行住宿怎么选？分享我的经验：

选择这家酒店的主要原因：
1. 位置好，去主要景点都方便
2. 口碑不错，评价很真实
3. 性价比可以，配套对得起价格

住了几天，整体感受超出预期。"""
    ]
    
    return random.choice(templates)


def generate_general_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """生成通用场景内容"""
    import random
    
    templates = [
        f"""发现了一个{topic}的好地方，必须分享出来：

去了才知道，真的很值得一来。
具体怎么样呢？往下看~

✨ 亮点分享：
- 体验感很棒
- 适合拍照打卡
- 值得多次打卡

整体来说，是一次不错的体验，推荐！""",
        
        f"""关于{topic}，我有话要说：

去之前做了很多功课，最终选了这里。
实际体验下来，有几点超预期：
1. 氛围感很强
2. 出片率高
3. 服务周到

想去的可以参考~"""
    ]
    
    return random.choice(templates)


def generate_product_embedding(topic: str, features: dict) -> str:
    """自然植入产品信息"""
    import random
    
    embeddings = [
        f"这次住的{topic}，整体体验下来感觉不错，感兴趣的可以了解一下~",
        f"{topic}的服务和配套都比较完善，适合家庭出行。",
        f"总体来说，{topic}是个值得考虑的选择。",
    ]
    
    return random.choice(embeddings)


def _generate_feature_based_content(topic: str, features: dict, topic_keywords: list = None) -> str:
    """基于提取的特征生成内容（黄金 5 段式）"""
    sections = []
    seen_content = set()
    topic_words = topic.split()
    
    # 相关地名
    related_places = {
        '西双版纳': ['告庄', '星光夜市', '曼听公园', '总佛寺', '野象谷', '植物园', '傣族园', '基诺山', '雨林', '告庄西双景', '景洪', '澜沧江', '大金塔', '江边夜市', '曼远村', '热带雨林谷'],
        '千岛湖': ['天屿山', '千岛湖大桥', '骑龙巷', '啤酒小镇', '灯塔', '东南湖区', '中心湖区', '梅峰岛', '黄山尖', '千岛湖'],
    }
    topic_related = related_places.get(topic, [])
    
    def is_relevant(text):
        if not text or len(text) < 15:
            return False
        for word in topic_words:
            if len(word) > 1 and word in text:
                return True
        for place in topic_related:
            if place in text:
                return True
        if len(text) > 50:
            return True
        return False
    
    def clean_text(text):
        import re
        # 移除话题标签
        text = re.sub(r'#\w+[话题]#', '', text)
        text = re.sub(r'\[\w+R\]', '', text)
        text = re.sub(r'\d+[️⃣]', '', text)
        return text.strip()
    
    def add_unique(items, max_count=4):
        result = []
        import random
        shuffled = items.copy()
        random.shuffle(shuffled)
        for item in shuffled:
            clean = clean_text(item)
            if clean and clean not in seen_content and len(clean) > 20:
                seen_content.add(clean)
                result.append(clean)
                if len(result) >= max_count:
                    break
        return result
    
    # 筛选相关特征
    relevant_vps = [vp for vp in features.get('value_points', []) if is_relevant(vp)]
    relevant_scenes = [sc for sc in features.get('scenes', []) if is_relevant(sc)]
    relevant_pains = [pp for pp in features.get('pain_points', []) if is_relevant(pp)]
    
    # 1. 痛点/引入
    if relevant_pains:
        pains = add_unique(relevant_pains, 1)
        if pains:
            sections.append(pains[0])
    
    if len(sections) == 0:
        sections.append(f"关于{topic}，我有一些真实体验想分享...")
    
    # 2. 解决方案引入
    sections.append(f"这次在{topic}的体验，完全超出预期！")
    
    # 3. 核心价值
    if relevant_vps:
        vps = add_unique(relevant_vps, 4)
        emojis = ["✅", "⭐️", "🎯", "💎", "✨", "🌟"]
        for i, vp in enumerate(vps):
            sections.append(f"{emojis[i % len(emojis)]} {vp}")
    else:
        sections.append(f"✨ {topic}的体验真的很棒")
        sections.append("🎯 细节到位，服务周到")
    
    # 4. 使用场景
    sections.append("")
    sections.append("推荐在这些时候选择：")
    
    if relevant_scenes:
        scenes = add_unique(relevant_scenes, 3)
        for scene in scenes:
            sections.append(f"• {scene}")
    else:
        sections.append("• 周末短途放松")
        sections.append("• 假期深度体验")
    
    # 5. 行动号召
    sections.append("")
    sections.append(f"关于{topic}，有问题欢迎评论区留言！")
    
    return "\n\n".join(sections)
