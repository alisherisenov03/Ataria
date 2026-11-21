# Финансы Алишера: правила для любого чата Claude

Все деньги учитываются в **одной** базе Supabase, проект `pepexjsboutlqmqjyemc`. Её читают и пишут:
- приложение «Финансы» на iPhone (папка `finance/`, https://alisher-finance.vercel.app), включая его поле умного ввода;
- чат «Финансы» (Claude Code);
- чат Kaspi и его «Ataria кабинет»;
- любой другой чат Алишера (СФК и т.д.).

Чаты не пишут друг другу напрямую. Общая база и есть их общий разговор: один записал, остальные прочитали.

## Кто чем владеет
| Что | Хозяин | Где лежит |
|---|---|---|
| Деньги **компании** Ataria: счёт компании, резерв, инвестор, платежи заводу, расходы компании, долги компании Алишеру, P&L | **Кабинет Kaspi** | Своё хранилище кабинета, зеркало в `jarvis.cabinet_snapshot` (id `ataria`) |
| Продажи Kaspi | Синхронизация заказов | `jarvis.kaspi_orders`, `jarvis.kaspi_items` |
| Личные деньги Алишера: Kaspi Gold, депозит, наличные, другие банки | **Приложение «Финансы»** | `public.fin_*` |

Правило: каждую сумму ведёт только её хозяин, остальные её читают. Поэтому ничего не задваивается.

## Таблицы приложения (схема `public`)
| Таблица / функция | Что хранит |
|---|---|
| `fin_accounts` | Счета: `kaspi-gold`, `kaspi-pay` (= **счёт компании**, `balance_source='cabinet'`: баланс берётся из кабинета), `kaspi-deposit`, `cash`, `other-bank` |
| `fin_account_balances` | Текущий баланс каждого счёта |
| `fin_projects` | `personal`, `pillows`, `combines`, `choppers`, `ads`, `business` |
| `fin_categories` | Категории расходов и доходов |
| `fin_transactions` | Операции. Важные поля: `company` (относится к компании), `cabinet_status` (`pending` → ждёт кабинета, `synced` → уже в кабинете, `skipped` → кабинету не нужно), `cabinet_ref` (id записи в кабинете), `source`, `receipt_path` (чек в bucket `fin-receipts`), `inbox_id` |
| `fin_inbox` | Всё, что Алишер написал, надиктовал или прислал в поле умного ввода, и что с этим сделал ИИ |
| `fin_budgets` | Месячные лимиты |
| `fin_company()` | Сводка из кабинета: `cash`, `reserve`, `owner_debt`, `owner_loans`, `upcoming`, `expenses`, `pnl_month` |
| `fin_kaspi_monthly(p_from)` | Продажи Kaspi по месяцам и проектам |

## Обмен с кабинетом Kaspi
**Приложение → кабинет.** Каждая операция компании, записанная в приложении, получает `cabinet_status = 'pending'`. Так же помечается любая операция со счётом компании, в том числе перевод со счёта компании на карту Алишера (возврат долга). Чат Kaspi при каждом обновлении кабинета делает так:
```sql
select t.*, a.slug account, ta.slug to_account, p.slug project, c.name category
from public.fin_transactions t
join public.fin_accounts a on a.id = t.account_id
left join public.fin_accounts ta on ta.id = t.to_account_id
left join public.fin_projects p on p.id = t.project_id
left join public.fin_categories c on c.id = t.category_id
where t.cabinet_status = 'pending' order by t.occurred_on;
```
- Если `cabinet_ref` пустой, это новая запись: добавить её в кабинет. Оплачена с личного счёта (`kaspi-gold`, `cash` и т.п.) → это расход компании и долг компании Алишеру (`paidBy: alisher`). Оплачена со счёта компании → расход из денег компании. Перевод `kaspi-pay → kaspi-gold` → возврат долга Алишеру (отметить в `owner_loans`).
- Если `cabinet_ref` заполнен, запись изменили в приложении: обновить её в кабинете.
- После этого: `update public.fin_transactions set cabinet_status='synced', cabinet_ref='<id в кабинете>' where id=...`.
- Если записи в кабинете не место: `cabinet_status='skipped'`.

**Кабинет → приложение.** Ничего копировать не нужно: приложение и ИИ читают `jarvis.cabinet_snapshot` через `fin_company()`. Кабинету достаточно обновлять снимок после каждого изменения, как он уже делает.

## Как записывать из любого чата
1. Личная трата, доход или перевод между личными счетами: строка в `fin_transactions` с `source = '<имя чата>'`.
2. Трата компании: в кабинет её вносит чат Kaspi. Другой чат пишет её в `fin_transactions` с `company = true`, `cabinet_status = 'pending'`, а кабинет заберёт её сам.
3. Перед записью проверьте дубль в `fin_transactions` **и** в `fin_company()->'expenses'` / `'upcoming'`.
4. **Продажи Kaspi вручную не вносите.**
5. Перевод между своими счетами — это `type='transfer'`, а не расход.
6. Если Алишер назвал текущий остаток личного счёта, обновите `opening_balance` и поставьте `opening_date = текущая дата` (с учётом сегодняшних операций). Остаток счёта компании меняется только в кабинете.
7. Не храните полные номера карт, CVV, пароли и коды из SMS.

## Как отвечать на вопросы о деньгах
- По компании отвечайте цифрами из `fin_company()`: деньги, резерв, прибыль за месяц и прогноз, долг компании Алишеру, ближайшие платежи.
- По личным деньгам — из `fin_account_balances` и `fin_transactions`.
- Отвечайте цифрами и давайте конкретный совет.
