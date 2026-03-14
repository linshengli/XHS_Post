# 🚀 小红书笔记自动生成系统

> 每天自动生成 10 篇高质量小红书图文笔记，结合 AI 图片识别 + 热门内容分析 + 爆款文案公式

## 📋 目录结构

```
~/XHS_Post/
├── scripts/                    # 核心脚本
│   ├── 01_analyze_images.py    # 图片智能分析
│   ├── 02_analyze_trending.py  # 热门内容分析
│   ├── 03_generate_posts.py    # 笔记生成引擎
│   └── run_daily_pipeline.sh   # 每日自动化执行
├── config/                     # 配置文件
│   ├── image_analysis.json     # 图片分析结果
│   ├── trending_analysis.json  # 热门分析结果
│   └── generation_state.json   # 生成状态（去重）
├── generated_posts/            # 生成的笔记
│   └── YYYY-MM-DD/            # 按日期分类
│       └── post_001.md ~ post_010.md
├── local_images/              # 本地图片库
│   └── 太空修/               # 太空主题图片
└── xhs_post_from_search/      # 爬取的热门数据
    └── json/
        └── search_contents_*.json
```

## ⚡ 快速开始

### 一键执行（推荐）

```bash
cd ~/XHS_Post
./scripts/run_daily_pipeline.sh
```

### 分步执行

```bash
# 1. 分析图片
python3 scripts/01_analyze_images.py

# 2. 分析热门内容
python3 scripts/02_analyze_trending.py

# 3. 生成 10 篇笔记
python3 scripts/03_generate_posts.py
```

## 🎯 核心功能

### 1️⃣ 图片智能分析 (`01_analyze_images.py`)

- **输入**: `local_images/太空修/` 下的所有图片
- **输出**: `config/image_analysis.json`
- **分析维度**:
  - 主题识别
  - 元素提取
  - 色彩分析
  - 情感氛围
  - 风格类型
  - 适用内容类型

**智能降级方案**: 当 OpenClaw image 工具不可用时，自动使用基于图片特征的智能推断。

### 2️⃣ 热门内容分析 (`02_analyze_trending.py`)

- **输入**: `xhs_post_from_search/json/search_contents_*.json`
- **输出**: `config/trending_analysis.json`
- **分析内容**:
  - 🔥 高赞笔记特征统计（点赞>3000）
  - 🏷️ 热门标签提取
  - 📝 标题公式分析
  - 📊 内容结构解析
  - 💬 互动话术总结
  - ⏰ 最佳发布时间建议

### 3️⃣ 笔记生成引擎 (`03_generate_posts.py`)

- **输入**: 
  - 图片分析结果
  - 热门分析结果
  - 历史生成状态
- **输出**: `generated_posts/YYYY-MM-DD/post_001.md ~ post_010.md`
- **生成特点**:
  - ✅ 3-5 个爆款标题（数字式/对比式/痛点式/好奇式/价值式）
  - ✅ 黄金 5 段式正文（痛点→方案→价值→场景→行动）
  - ✅ 丰富的 Emoji 表情
  - ✅ 10-15 个精准标签
  - ✅ 3-9 张图片智能分配
  - ✅ 最佳发布时间建议
  - ✅ 去重机制（图片组合不重复）

## 📝 输出示例

每篇笔记包含：

```markdown
# 🔥 标题选项 (4 个)
1. 🚀 3 个技巧，让你的视觉效果提升
2. ✨ 从拍照普通到大片质感，我只做了 1 件事
3. 🎯 摄影爱好者必看！解决你的构图没思路
4. 💯 纯干货！太空摄影看这一篇就够了

## 🏷️ 推荐标签
#太空摄影 #星空拍摄 #宇宙美学 #视觉艺术 ...

## 📸 配图 (6 张)
1. ~/XHS_Post/local_images/太空修/xxx.jpg (封面)
2. ...

## ✍️ 正文

[痛点引入]
每次仰望星空，都觉得自己好渺小...

[解决方案]
今天分享的这组太空图片，让你近距离感受宇宙的魅力！

[核心价值]
为什么这些图片这么震撼？因为：
✨ 科普价值，了解宇宙的窗口
💫 艺术价值，科学与美学的完美结合
✅ 高清画质，细节清晰可见

[使用场景]
推荐给以下人群：
• 摄影爱好者
• 太空迷
• 视觉控

[行动号召]
觉得震撼记得点赞分享哦！

## ⏰ 最佳发布时间
晚上 18:00-20:00 (晚高峰)
```

## 🔁 去重机制

系统通过 `generation_state.json` 记录：

- ✅ 已使用的图片组合 ID
- ✅ 每日生成历史
- ✅ 累计生成数量

确保：
- 每天的图片组合不重复
- 内容主题不重复
- 可持续长期运行

## ⏰ 定时任务设置

### 方式一：Cron（推荐）

```bash
# 编辑 crontab
crontab -e

# 添加每日早上 6 点执行
0 6 * * * cd ~/XHS_Post && ./scripts/run_daily_pipeline.sh >> ~/XHS_Post/logs/cron.log 2>&1
```

### 方式二：系统定时器

创建 systemd service 和 timer（Linux）

## 📊 数据统计

查看生成统计：

```bash
# 查看生成状态
cat config/generation_state.json

# 查看今日生成的笔记
ls -la generated_posts/$(date +%Y-%m-%d)/

# 查看分析结果
cat config/trending_analysis.json | jq .
```

## 🔧 自定义配置

### 更换图片主题

1. 替换 `local_images/太空修/` 下的图片
2. 更新 `scripts/01_analyze_images.py` 中的主题模板
3. 重新运行图片分析

### 调整内容风格

编辑 `scripts/03_generate_posts.py` 中的：
- `SPACE_CONTENT_TEMPLATES` - 内容模板
- `TITLE_TEMPLATES` - 标题公式
- `SPACE_THEMES` - 主题词库

### 修改生成数量

在 `scripts/03_generate_posts.py` 中修改：

```python
# 将 10 改为你想要的数量
for i in range(1, 11):  # 改为 range(1, 21) 生成 20 篇
```

## 🛠️ 故障排查

### 问题 1: 图片分析失败

**现象**: 图片分析结果为空或全是"待分析"

**解决**:
```bash
# 检查图片文件
ls -la ~/XHS_Post/local_images/太空修/

# 手动测试图片分析
python3 scripts/01_analyze_images.py
```

### 问题 2: 热门数据缺失

**现象**: trending_analysis.json 为空

**解决**:
```bash
# 检查数据文件
ls -la ~/XHS_Post/xhs_post_from_search/json/

# 确保文件存在且格式正确
cat search_contents_*.json | head -20
```

### 问题 3: 笔记内容重复

**现象**: 生成的笔记内容相似度高

**解决**:
```bash
# 清空去重状态（谨慎使用）
cat > config/generation_state.json << 'EOF'
{
  "last_run": null,
  "total_posts_generated": 0,
  "used_combinations": [],
  "daily_history": []
}
EOF
```

## 📈 优化建议

### 内容质量提升

1. **接入真实 AI 图片分析**: 修复 OpenClaw image 工具的 API 密钥
2. **使用 LLM 生成文案**: 调用 ChatGPT/Claude 等生成更自然的内容
3. **增加主题多样性**: 添加更多图片主题文件夹

### 发布自动化

1. **接入小红书 API**: 自动发布生成的笔记
2. **定时发布**: 在最佳发布时间自动推送
3. **数据反馈**: 根据发布数据优化生成策略

### 扩展主题

复制整个目录结构，创建不同主题的生成系统：
- `~/XHS_Post_travel/` - 旅行主题
- `~/XHS_Post_food/` - 美食主题
- `~/XHS_Post_tech/` - 科技主题

## 📄 日志管理

日志文件位置：
```
~/XHS_Post/logs/pipeline_YYYY-MM-DD.log
```

查看今日日志：
```bash
tail -f ~/XHS_Post/logs/pipeline_$(date +%Y-%m-%d).log
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个系统！

## 📄 License

MIT License

---

**🎉 祝你每天都能生成爆款小红书笔记！**
