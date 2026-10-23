"""Instagram analytics through Windsor.ai (read only). Needs WINDSOR_API_KEY; no Meta app review required."""
import httpx

import config

FIELDS = ["date", "media_type", "media_caption", "media_permalink", "media_reach", "media_views",
          "media_like_count", "media_comments_count", "media_saved", "media_shares"]


def stats(days: int = 30) -> dict:
    if not config.WINDSOR_API_KEY:
        return {"error": "Instagram не подключён: в Vercel нужна переменная WINDSOR_API_KEY (ключ из кабинета Windsor.ai)"}
    days = max(1, min(int(days or 30), 90))
    base = "https://connector.windsor.ai/instagram"
    posts = httpx.get(base, params={"api_key": config.WINDSOR_API_KEY, "date_preset": f"last_{days}d",
                                    "fields": ",".join(FIELDS)}, timeout=40)
    if posts.status_code != 200:
        return {"error": f"Windsor {posts.status_code}: {posts.text[:200]}"}
    rows = posts.json().get("data", [])
    for r in rows:
        r["media_caption"] = (r.get("media_caption") or "")[:90].replace("\n", " ")
    acc = httpx.get(base, params={"api_key": config.WINDSOR_API_KEY, "date_preset": "last_3d",
                                  "fields": "account_name,followers_count,media_count"}, timeout=30)
    account = (acc.json().get("data") or [{}])[0] if acc.status_code == 200 else {}
    rows.sort(key=lambda r: -(r.get("media_reach") or 0))
    return {"account": account, "posts": rows[:15], "total_posts": len(rows),
            "avg_reach": round(sum((r.get("media_reach") or 0) for r in rows) / len(rows)) if rows else 0}
