---
name: competitor-watch
description: Track competitors of Ataria products on Kaspi and Instagram: price moves, new sellers, rating and review growth. Use weekly or for "что у конкурентов", "кто демпингует".
---

# Competitor watch

1. For each Ataria product query (planetary mixer 7 L, orthopedic pillow 40x60 / 35x60, kitchen grinder): `kaspi_market.search` top 10 and `offers` for our product id.
2. Compare with the last saved snapshot in `jarvis.memory` (dated fact): price change, new sellers on our card, review count growth.
3. Instagram/TikTok: vidIQ outliers for the niche (5 credits each) only when asked or monthly.
4. Save a new dated fact; report only changes that matter (> 5% price, new seller under our price, competitor review jump).
