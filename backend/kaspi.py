"""Kaspi Магазин → jarvis.kaspi_* (port of the old kaspi-sync service).

One call = one bounded pass, so it works on serverless too. Progress is kept in
jarvis.kaspi_sync_state; if the time budget runs out the next call continues.
"""
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout, as_completed
from datetime import datetime, timezone

import httpx

import config
import db

BASE = "https://kaspi.kz/shop/api/v2"
DAY = 86_400_000
WINDOW = 14 * DAY  # Kaspi returns orders in windows of at most 14 days
WORKERS = 5
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


def _entries(http, order_id: str):
    """Order lines as kaspi_items rows, or None if the call failed. No DB writes."""
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
    return rows


def _fetch_many(http, order_ids: list[str], deadline: float) -> dict[str, list[dict]]:
    """Fetch order lines concurrently; orders not finished before the deadline are simply absent."""
    out: dict[str, list[dict]] = {}
    if not order_ids:
        return out
    ex = ThreadPoolExecutor(max_workers=WORKERS)
    futs = {ex.submit(_entries, http, oid): oid for oid in order_ids}
    try:
        for f in as_completed(futs, timeout=max(1.0, deadline - time.time())):
            rows = f.result()
            if rows is not None:
                out[futs[f]] = rows
    except FuturesTimeout:
        pass
    finally:
        ex.shutdown(wait=False, cancel_futures=True)
    return out


def _save_items(fetched: dict[str, list[dict]]):
    rows = [r for items in fetched.values() for r in items]
    if rows:
        db.client().table("kaspi_items").upsert(rows, on_conflict="entry_id").execute()


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
            need = [i for i in ids if known.get(i) is None]
            fetched = _fetch_many(http, need, deadline)
            _save_items(fetched)
            batch = []
            for o in rows:
                a = o.get("attributes") or {}
                qty = known.get(o["id"])
                if qty is None and o["id"] in fetched:
                    qty = sum(r["qty"] for r in fetched[o["id"]])
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


def _backfill_items(http, deadline: float) -> int:
    """Orders saved without their lines (budget ran out earlier): fill them in, newest first."""
    ids = [r["id"] for r in db.client().table("kaspi_orders").select("id")
           .is_("qty", "null").order("created_at", desc=True).limit(150).execute().data]
    fetched = _fetch_many(http, ids, deadline)
    _save_items(fetched)
    for oid, items in fetched.items():
        db.client().table("kaspi_orders").update({"qty": sum(r["qty"] for r in items)}).eq("id", oid).execute()
    return len(fetched)


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
        backfilled = _backfill_items(http, deadline) if time.time() < deadline else 0
    db.client().table("kaspi_sync_state").upsert({"key": "last_to", "value": str(now)}).execute()
    db.log_action("kaspi", "kaspi_sync", "sync", {"deep": deep}, {"orders": total, "errors": errors}, not errors)
    return {"complete": True, "orders_saved": total, "items_backfilled": backfilled, "errors": errors}


def daily_sales(days: int = 14) -> list[dict]:
    return (db.client().table("kaspi_daily_sales").select("*")
            .order("day", desc=True).limit(max(1, min(days, 120))).execute().data)


PARTNER_NOTE = "товары партнёра (owner ≠ alisher) не включены"


def _setting(key: str):
    rows = db.client().table("settings").select("value").eq("key", key).execute().data
    return rows[0]["value"] if rows else None


def set_setting(key: str, value: str) -> dict:
    db.client().table("settings").upsert({"key": key, "value": str(value), "updated_at": "now()"}).execute()
    return {"saved": key, "value": value}


def profit(date_from: str, date_to: str, include_partner: bool = False) -> dict:
    """Revenue, cost and gross profit for Almaty dates [date_from, date_to] (YYYY-MM-DD)."""
    rows = db.client().rpc("kaspi_product_sales", {"p_from": date_from, "p_to": date_to}).execute().data
    partner = [r for r in rows if r["owner"] != "alisher"]
    mine = rows if include_partner else [r for r in rows if r["owner"] == "alisher"]
    revenue = sum(float(r["revenue"] or 0) for r in mine)
    with_cost = [r for r in mine if r["unit_cost"] is not None]
    missing = [{"code": r["product_code"], "name": r["product_name"], "units": r["units"], "revenue": float(r["revenue"])}
               for r in mine if r["unit_cost"] is None]
    cost = sum(float(r["unit_cost"]) * r["units"] for r in with_cost)
    fee_pct = _setting("kaspi_fee_percent")
    fee = revenue * float(fee_pct) / 100 if fee_pct is not None else None
    complete = not missing and fee is not None
    return {
        "period": [date_from, date_to],
        "orders_revenue": round(revenue),
        "cost_of_goods_known": round(cost),
        "kaspi_fee_percent": float(fee_pct) if fee_pct is not None else None,
        "kaspi_fee": round(fee) if fee is not None else None,
        "gross_profit": round(revenue - cost - fee) if complete else None,
        "products": [{"name": r["product_name"], "code": r["product_code"], "units": r["units"],
                      "revenue": round(float(r["revenue"])), "unit_cost": r["unit_cost"]} for r in mine[:10]],
        "missing_cost": missing,
        "excluded_partner_products": [r["product_name"] for r in partner] if not include_partner else [],
        "notes": ("Реклама и доставка не вычтены. " + (PARTNER_NOTE if partner and not include_partner else "")
                  + ("" if complete else " Прибыль не посчитана: не хватает себестоимости товаров или комиссии Kaspi.")).strip(),
    }


def set_cost(product: str, unit_cost: float) -> dict:
    """Find the product by code or by part of its name, then store its unit cost."""
    q = product.strip()
    rows = db.client().table("kaspi_items").select("product_code,product_name").eq("product_code", q).limit(1).execute().data
    if not rows:
        rows = db.client().table("kaspi_items").select("product_code,product_name").ilike("product_name", f"%{q}%").limit(200).execute().data
    found = {r["product_code"]: r["product_name"] for r in rows if r["product_code"]}
    if not found:
        return {"error": f"не нашёл товар «{product}»"}
    if len(found) > 1:
        return {"ambiguous": [{"code": c, "name": n} for c, n in found.items()],
                "hint": "уточни, какой из товаров (по коду или точному названию)"}
    code, name = next(iter(found.items()))
    db.client().table("kaspi_costs").upsert({"product_code": code, "product_name": name,
                                            "unit_cost": unit_cost, "updated_at": "now()"}).execute()
    return {"saved": {"code": code, "name": name, "unit_cost": unit_cost}}
