---
name: kaspi-pricing
description: Decide a Kaspi price for an Ataria product: floor price, target-margin price, competitor position, effect on sales. Use for "поднять/снизить цену", "почему упали продажи после повышения", "какую цену ставить".
---

# Kaspi pricing

1. Unit economics at the current and candidate prices (kaspi-unit-economics). Floor = price where profit after ads is 0; target = price for the chosen margin (cabinet default 20%).
2. Competitors: `kaspi_market.search` / `offers` for the same query; note price, rating, review count, number of sellers. Fewer reviews than the leader means price must compensate.
3. History: compare units per week before and after past price changes (jarvis.kaspi_daily_sales). Known: SM23 sales fell after the move from 109 990 to higher prices; pillow 35x60 vs LARKO 14 990, DS 10 700, NikStory 7 300.
4. Thresholds: crossing 10 000 ₸ changes Kaspi delivery (799 → 1299+VAT): grinders at 9 990 must stay below 10 000.
5. Answer: recommended price, expected profit per unit and per week at current volume, risk, and how to test (change for 7 days, then kaspi_analytics).
Price changes in the Kaspi cabinet are made by Alisher.
