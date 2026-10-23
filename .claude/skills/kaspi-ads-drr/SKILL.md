---
name: kaspi-ads-drr
description: Analyse Kaspi advertising: spend, DRR (ads share of revenue), cost per sale by product; recommend bids to cut or raise. Use for "реклама", "ДРР", "где сливаем деньги", "сколько ставить".
---

# Kaspi ads and DRR

Data: ad reports in the cabinet (`cabinet_snapshot.data.ads`: date or date range, total, lines per product), sales from Kaspi tables.

Per product: ad spend per sale = spend / units; DRR = spend / revenue. Compare with profit per unit before ads.
- Ads per sale > profit before ads: losing money on every sale → cut or stop (e.g. Oct 2026: AT-1100 3 061 ₸ per sale vs 797 ₸ profit, AT-2300 6 906 ₸).
- DRR above target (15%) but positive profit: lower bids gradually.
- Low stock (< 7 days of sales): pause ads, it will sell anyway.
Output a table product | spend | per sale | DRR | profit after ads | action. Bids are changed by Alisher in Kaspi.
