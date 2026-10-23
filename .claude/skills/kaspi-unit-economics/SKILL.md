---
name: kaspi-unit-economics
description: Compute exact per-unit and per-period profit for an Ataria product on Kaspi. Use for "сколько зарабатываем с штуки", "прибыль", "маржа", "выгодно ли", before any price or purchase decision.
---

# Kaspi unit economics

Source of truth: "Ataria кабинет" artifact, mirrored to `jarvis.cabinet_snapshot` (id `ataria`), and `jarvis.kaspi_costs` + RPC `jarvis.kaspi_product_economics(date,date)`.

Per unit = price − landed cost (factory + cargo from purchase batches) − Kaspi fee (pillows 10.9%, appliances 11.3%) − Kaspi delivery − packaging − returns reserve − own delivery − rent share − tax 3% − ads (DRR target 15%, actual from ad reports).

Kaspi delivery 2026 (excl. VAT, +16%): price < 10 000 ₸: ≤1000 → 49, ≤3000 → 149, ≤5000 → 199, else 799 (city 699). Price ≥ 10 000 ₸ by weight: ≤5 kg 1299, ≤15 kg 1699, ≤30 kg 3599, ≤60 kg 5649, ≤100 kg 8549, else 11999 (city: 1099/1349/2299/2899/4149/6449).

Rules: periods use the Kaspi business day (after 16:00 Almaty = next day). Partner products (jarvis.kaspi_product_owner owner ≠ alisher) are excluded unless asked. Purchase prices marked "оценка" in the cabinet must be called estimates. Never invent a cost: if missing, say which product lacks it.
