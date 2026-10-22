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


def sync(deep: bool = False, budget_s: int = 50, quick: bool = False) -> dict:
    """quick = only the last 2 days, for the every-minute run (no progress bookkeeping)."""
    if not config.KASPI_TOKEN:
        return {"error": "KASPI_TOKEN is not set"}
    deadline = time.time() + (40 if quick else budget_s)
    now = int(time.time() * 1000)
    last = _state("last_to")
    if quick:
        frm = now - 2 * DAY
    elif last:
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
        backfilled = _backfill_items(http, deadline) if time.time() < deadline and not quick else 0
    if quick:
        return {"complete": True, "quick": True, "orders_saved": total, "errors": errors}
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


# Kaspi delivery tariffs from 2026-01-01 (excl. VAT), same table as the "Ataria кабинет" page.
KASPI_VAT = 0.16
WEIGHT_KG = {"656185779": 12}  # everything else ships as 1.5–3 kg


def kaspi_delivery(price: float, kg: float = 3) -> float:
    if price < 10000:
        t = 49 if price <= 1000 else 149 if price <= 3000 else 199 if price <= 5000 else 799
    else:
        t = 1299 if kg <= 5 else 1699 if kg <= 15 else 3599 if kg <= 30 else 5649 if kg <= 60 else 8549 if kg <= 100 else 11999
    return t * (1 + KASPI_VAT)


def profit(date_from: str, date_to: str, include_partner: bool = False) -> dict:
    """Profit for Kaspi business days [date_from, date_to] (YYYY-MM-DD), per-product economics from jarvis.kaspi_costs."""
    rows = db.client().rpc("kaspi_product_economics", {"p_from": date_from, "p_to": date_to}).execute().data
    partner = [r for r in rows if r["owner"] != "alisher"]
    mine = rows if include_partner else [r for r in rows if r["owner"] == "alisher"]
    tax_pct = float(_setting("tax_percent") or 0)
    default_fee = _setting("kaspi_fee_percent")
    products, missing = [], []
    tot = dict(revenue=0.0, cost=0.0, fee=0.0, tax=0.0, returns=0.0, pack=0.0, delivery=0.0)
    for r in mine:
        units, revenue = int(r["units"] or 0), float(r["revenue"] or 0)
        fee_pct = r["fee_percent"] if r["fee_percent"] is not None else default_fee
        if r["unit_cost"] is None or fee_pct is None or not units:
            missing.append({"code": r["product_code"], "name": r["product_name"], "units": units, "revenue": round(revenue)})
            continue
        price = revenue / units
        line = dict(revenue=revenue, cost=float(r["unit_cost"]) * units, fee=revenue * float(fee_pct) / 100,
                    tax=revenue * tax_pct / 100, returns=revenue * float(r["return_percent"] or 0) / 100,
                    pack=float(r["pack_cost"] or 0) * units,
                    delivery=kaspi_delivery(price, WEIGHT_KG.get(r["product_code"], 3)) * units)
        for k, v in line.items():
            tot[k] += v
        p = revenue - sum(v for k, v in line.items() if k != "revenue")
        products.append({"name": r["product_name"], "code": r["product_code"], "units": units, "revenue": round(revenue),
                         "unit_cost": float(r["unit_cost"]), "cost_is_estimate": r["cost_is_estimate"],
                         "profit": round(p), "profit_per_unit": round(p / units)})
    gross = tot["revenue"] - sum(v for k, v in tot.items() if k != "revenue")
    estimates = [p["name"] for p in products if p["cost_is_estimate"]]
    return {
        "period": [date_from, date_to],
        "orders_revenue": round(tot["revenue"] + sum(m["revenue"] for m in missing)),
        "counted_revenue": round(tot["revenue"]),
        "cost_of_goods": round(tot["cost"]),
        "kaspi_fee": round(tot["fee"]),
        "kaspi_delivery": round(tot["delivery"]),
        "tax": round(tot["tax"]),
        "returns_reserve": round(tot["returns"]),
        "packaging": round(tot["pack"]),
        "profit_before_ads": round(gross),
        "products": products[:12],
        "missing_cost": missing,
        "excluded_partner_products": [r["product_name"] for r in partner] if not include_partner else [],
        "notes": " ".join(filter(None, [
            "Себестоимость из «Ataria кабинет» (партии закупа). Реклама, аренда склада и своя доставка до Kaspi не вычтены.",
            ("Закуп оценочный у: " + ", ".join(estimates) + ".") if estimates else "",
            PARTNER_NOTE if partner and not include_partner else "",
            "Без себестоимости не посчитаны: " + ", ".join(m["name"] for m in missing) + "." if missing else "",
        ])),
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


def last_synced_at():
    rows = db.client().table("kaspi_orders").select("synced_at").order("synced_at", desc=True).limit(1).execute().data
    return rows[0]["synced_at"] if rows else None


def open_orders() -> list[dict]:
    """Accepted orders not yet handed to the courier (what the Kaspi cabinet shows as in progress)."""
    rows = (db.client().table("kaspi_orders").select("code,created_at,total_price,raw")
            .neq("state", "ARCHIVE").eq("status", "ACCEPTED_BY_MERCHANT")
            .order("created_at").limit(200).execute().data)
    out = []
    for r in rows:
        delivery = ((r.get("raw") or {}).get("attributes") or {}).get("kaspiDelivery") or {}
        if delivery.get("courierTransmissionDate"):
            continue
        out.append({"code": r["code"], "created_at": r["created_at"], "total": r["total_price"]})
    return out
