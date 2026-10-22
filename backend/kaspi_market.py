"""Public Kaspi storefront: search products and seller offers (prices, ratings, reviews) for market research."""
import httpx

ALMATY = "750000000"
HEADERS = {"Accept": "application/json, text/*", "User-Agent": "Mozilla/5.0", "Referer": "https://kaspi.kz/shop/search/"}


def search(text: str, limit: int = 12) -> list[dict]:
    r = httpx.get("https://kaspi.kz/yml/product-view/pl/results", headers=HEADERS, timeout=20, params={
        "page": 0, "q": ":availableInZones:Magnum_ZONE1", "text": text, "sort": "relevance",
        "ui": "d", "i": -1, "c": ALMATY})
    r.raise_for_status()
    return [{"id": it.get("id"), "title": it.get("title"), "price": it.get("unitPrice"),
             "rating": it.get("rating"), "reviews": it.get("reviewsQuantity"),
             "url": f"https://kaspi.kz/shop/p/-{it.get('id')}/"} for it in (r.json().get("data") or [])[:limit]]


def offers(product_id: str, limit: int = 10) -> list[dict]:
    r = httpx.post(f"https://kaspi.kz/yml/offer-view/offers/{product_id}", headers=HEADERS, timeout=20, json={
        "cityId": ALMATY, "id": str(product_id), "merchantUID": "", "limit": limit, "page": 0, "sort": True,
        "product": {"brand": "", "categoryCodes": [], "baseProductCodes": [], "groups": []},
        "zoneId": ["Magnum_ZONE1"], "installationId": "-1"})
    r.raise_for_status()
    return [{"merchant": o.get("merchantName"), "price": o.get("price"),
             "merchant_rating": o.get("merchantRating"), "merchant_reviews": o.get("merchantReviewsQuantity")}
            for o in (r.json().get("offers") or [])]
