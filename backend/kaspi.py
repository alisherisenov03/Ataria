"""Kaspi Магазин → jarvis.kaspi_* (port of the old kaspi-sync service).

One call = one bounded pass, so it works on serverless too. Progress is kept in
jarvis.kaspi_sync_state; if the time budget runs out the next call continues.
"""
import time
from datetime import datetime, timezone

import httpx

import config
import db

BASE = "https://kaspi.kz/shop/api/v2"
DAY = 86_400_000
WINDOW = 14 * DAY  # Kaspi returns orders in windows of at most 14 days
STATES = ["NEW", "SIGN_REQUIRED", "PICKUP", "DELIVERY", "KASPI_DELIVERY", "ARCHIVE"]


class _OutOfTime(Exception):
    pass


def _iso(ms) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()


def _http() -> httpx.Client:
    return httpx.Client(
        base_url=BASE, timeout=20,
        headers={"X-Auth-Token": config.KASPI_TOKEN,
                 "Content-Type": "application/vnd.api+json", "User-Agent": "jarvis-sync/1.0"},
    )


def _get(http: httpx.Client, path: str, params: dict) -> dict:
    r = http.get(path, params=params)
    if r.status_code != 200:
        raise RuntimeError(f"Kaspi {r.status_code} on {path}")
    return r.json()


def _fetch_items(http, order_id: str):
    """Order lines → kaspi_items. Returns total qty, or None if the call failed."""
    try:
        j = _get(http, f"/orders/{order_id}/entries", {"include[entries]": "product"})
    except Exception:
        return None
    included = {i["id"]: i for i in j.get("included", [])}
    rows = []
    for e in j.get("data", []):
        a = e.get("attributes") or {}
        pid = ((e.get("relationships") or {}).get("product") or {}).get("data", {}) or {}
        p = (included.get(pid.get("id")) or {}).get("attributes") or {}
        offer = a.get("offer") or {}
        rows.append({
            "entry_id": e["id"], "order_id": order_id,
            "product_code": offer.get("code") or p.get("code"),
            "product_name": offer.get("name") or p.get("name") or (a.get("category") or {}).get("title") or "без названия",
            "qty": a.get("quantity") or 0,
            "unit_price": a.get("basePrice") if a.get("basePrice") is not None else a.get("unitPrice"),
            "total_price": a.get("totalPrice"),
        })
    if rows:
        db.client().table("kaspi_items").upsert(rows, on_conflict="entry_id").execute()
    return sum(r["qty"] for r in rows)


def _sync_window(http, frm: int, to: int, state: str, deadline: float) -> int:
    page, saved = 0, 0
    while True:
        if time.time() > deadline:
            raise _OutOfTime
        j = _get(http, "/orders", {
            "page[number]": page, "page[size]": 100, "filter[orders][state]": state,
            "filter[orders][creationDate][$ge]": frm, "filter[orders][creationDate][$le]": to,
        })
        rows = j.get("data", [])
        if rows:
            ids = [o["id"] for o in rows]
            known = {r["id"]: r["qty"] for r in
                     db.client().table("kaspi_orders").select("id,qty").in_("id", ids).execute().data}
            batch = []
            for o in rows:
                if time.time() > deadline:
                    raise _OutOfTime
                a = o.get("attributes") or {}
                qty = known.get(o["id"])
                if qty is None:
                    qty = _fetch_items(http, o["id"])
                batch.append({
                    "id": o["id"], "code": a.get("code"), "state": a.get("state"), "status": a.get("status"),
                    "created_at": _iso(a["creationDate"]) if a.get("creationDate") else None,
                    "total_price": a.get("totalPrice"), "payment_mode": a.get("paymentMode"),
                    "qty": qty, "raw": o,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                })
            db.client().table("kaspi_orders").upsert(batch, on_conflict="id").execute()
            saved += len(batch)
        page += 1
        if page >= (j.get("meta") or {}).get("pageCount", 1) or not rows:
            return saved


def _state(key: str):
    r = db.client().table("kaspi_sync_state").select("value").eq("key", key).execute().data
    return r[0]["value"] if r else None


def sync(deep: bool = False, budget_s: int = 50) -> dict:
    if not config.KASPI_TOKEN:
        return {"error": "KASPI_TOKEN is not set"}
    deadline = time.time() + budget_s
    now = int(time.time() * 1000)
    last = _state("last_to")
    if last:
        frm = min(int(last) - DAY, now - (90 if deep else 14) * DAY)
    else:
        frm = now - config.KASPI_BACKFILL_DAYS * DAY
    total, errors = 0, []
    with _http() as http:
        try:
            while frm < now:
                to = min(frm + WINDOW, now)
                for state in STATES:
                    try:
                        total += _sync_window(http, frm, to, state, deadline)
                    except _OutOfTime:
                        raise
                    except Exception as e:
                        errors.append(f"{state}: {e}")
                frm = to
        except _OutOfTime:
            return {"complete": False, "orders_saved": total, "errors": errors,
                    "note": "time budget reached; call again to continue"}
    db.client().table("kaspi_sync_state").upsert({"key": "last_to", "value": str(now)}).execute()
    db.log_action("kaspi", "kaspi_sync", "sync", {"deep": deep}, {"orders": total, "errors": errors}, not errors)
    return {"complete": True, "orders_saved": total, "errors": errors}


def daily_sales(days: int = 14) -> list[dict]:
    return (db.client().table("kaspi_daily_sales").select("*")
            .order("day", desc=True).limit(max(1, min(days, 120))).execute().data)
