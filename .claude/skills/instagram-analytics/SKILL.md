---
name: instagram-analytics
description: Read and interpret Instagram performance for Ataria accounts: followers, reach, views, saves, shares per post; what worked and what to post next. Use for "как Instagram", "какие посты зашли", "статистика", "охваты".
---

# Instagram analytics

Access: Windsor.ai (`mcp__Windsor_ai__get_data`, connector `instagram`, account 17841466944137313 = @ataria.kz) and Metricool (brand 7592790). Jarvis uses Windsor REST with `WINDSOR_API_KEY` (`backend/instagram.py`).
@ataria.kz = combines/kitchen tech only; pillows are a separate account (connect it in Windsor/Metricool when available).

Read per post: reach, views, saves, shares, likes, comments, profile visits; account: followers. Judge by saves + shares per reach (intent) more than likes.
Baseline Oct 2026: 70 followers, 5 posts, reach 82–436, best = SM23 reel 23.09 (436 reach, 14 saves, 7 shares); carousels weaker; profile visits 2–4 per post.
Output: top and bottom posts with numbers, the pattern behind them, 3 next posts (use ataria-reels formula). Posting only after Alisher's "да".
