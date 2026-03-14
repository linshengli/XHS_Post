from xhs_post.topic import filter_posts_by_source_keyword, parse_like_count


def test_parse_like_count_supports_wan_suffix():
    assert parse_like_count("4.2万") == 42000
    assert parse_like_count("6800") == 6800
    assert parse_like_count("") == 0


def test_filter_posts_by_source_keyword_matches_core_topic():
    posts = [
        {"source_keyword": "千岛湖", "title": "千岛湖旅游攻略", "desc": "", "tag_list": ""},
        {"source_keyword": "北京", "title": "北京旅游攻略", "desc": "", "tag_list": ""},
    ]

    filtered = filter_posts_by_source_keyword(posts, "千岛湖旅游攻略")

    assert len(filtered) == 1
    assert filtered[0]["source_keyword"] == "千岛湖"
