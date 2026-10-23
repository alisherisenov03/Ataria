---
name: kaspi-daily-ops
description: Day-to-day Kaspi operations facts: what "today's orders" means, business-day cut-off, sync, packaging, returns. Use whenever counting orders, answering "сколько заказов сегодня", or debugging a mismatch with the Kaspi cabinet.
---

# Kaspi daily operations

- Business day: orders created after 16:00 Almaty belong to the next day (`(created_at at time zone 'Asia/Almaty') + interval '8 hours'`).
- "Today's orders" = orders in packaging for today's shipment (ACCEPTED_BY_MERCHANT, no courier transmission yet), split into ship today / ship tomorrow.
- Sync: pg_cron calls `/kaspi/sync?quick=1` every minute (last 2 days), deep sync every 6 h. Tables `jarvis.kaspi_orders`, `jarvis.kaspi_items`.
- Excluded from sales: CANCELLED/CANCELLING/RETURNED and orders under 1 000 ₸ (self-purchases).
- Mismatch with the cabinet: check `synced_at` freshness first, then status filters, then the 16:00 cut-off.
