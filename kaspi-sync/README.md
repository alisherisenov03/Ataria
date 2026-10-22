# ataria-kaspi-sync

Каждые 10 минут забирает заказы Kaspi Магазина и сохраняет в Postgres (таблица `kaspi_orders`, вид `daily_sales`).

Переменные в Railway:
- `KASPI_TOKEN` — токен из кабинета продавца (вставляется только в Railway, не в код и не в чат)
- `DATABASE_URL` — ссылка на Postgres из Railway (Reference Variable)
- `SYNC_MINUTES`, `BACKFILL_DAYS` — необязательно

Формат запросов написан по описанию Kaspi Shop API и ещё не проверен на реальном токене.
