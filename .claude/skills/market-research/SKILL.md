---
name: market-research
description: Research the market for Ataria: Kaspi competitors and prices, niches, global/CIS/Kazakhstan trends, suppliers. Use for "что сейчас в тренде", "найди нишу", "сравни с конкурентами", "что продавать", price decisions.
---

# Market research for Ataria

## Sources, in this order
1. Our numbers: Kaspi sales and profit (`kaspi_analytics` in Jarvis, cabinet mirror `jarvis.cabinet_snapshot`).
2. Kaspi storefront: `backend/kaspi_market.py` search/offers (price, rating, reviews, sellers).
3. Content trends: vidIQ outlier search (5 credits per call, 150 per month; say the cost).
4. Instagram performance: Windsor `instagram` connector (@ataria.kz).
5. Web: WebSearch for global, CIS and Kazakhstan, with dates.

## Output format
Three levels (world, CIS, Kazakhstan) with dated sources, then exactly 3 concrete ideas for Ataria, each with the number that supports it (price, sales, margin, views). Save the key findings to `jarvis.memory` as dated `fact` (memory-keeper rules).

## Rules
- Kaspi delivery tariff jumps at 10 000 ₸: price changes around that line need the full unit economics.
- Never state a market number without its source and date.
