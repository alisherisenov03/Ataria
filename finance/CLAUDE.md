# Финансы Алишера: правила для любого чата Claude

Все деньги (личные и бизнес) учитываются в **одной** базе Supabase, в проекте `pepexjsboutlqmqjyemc`.
Её читают и пишут все чаты (финансы, Kaspi, СФК и т.д.) и приложение «Финансы» на iPhone (папка `finance/` этого репозитория).
Чаты не обмениваются сообщениями напрямую. Синхронизация происходит так: один чат записал в базу, остальные прочитали.

## Таблицы (схема `public`)
| Таблица | Что хранит |
|---|---|
| `fin_accounts` | Счета: `kaspi-gold`, `kaspi-pay`, `kaspi-deposit`, `cash`, `other-bank`. У счёта есть `opening_balance` на дату `opening_date`, `interest_rate` (% годовых для депозита) и `last4` |
| `fin_account_balances` | Вьюха с текущим балансом каждого счёта (`balance`) |
| `fin_projects` | Проекты по `slug`: `personal` (Личное), `pillows` (Подушки), `combines` (Комбайны), `choppers` (Измельчители), `ads` (Реклама), `business` (Бизнес — общее) |
| `fin_categories` | Категории (`type` = `income` / `expense`) |
| `fin_transactions` | Операции: `type` = `income` / `expense` / `transfer`; `amount` > 0 в тенге; `occurred_on`; `account_id`; `to_account_id` (только для переводов); `project_id`; `category_id`; `note`; `source` |
| `fin_budgets` | Месячные лимиты по проекту и/или категории |
| `fin_kaspi_monthly(p_from)` | Продажи Kaspi по месяцам и проектам (выручка, комиссия, себестоимость). Считаются из `jarvis.kaspi_orders` |

## Как записывать
1. Узнали о расходе, доходе или переводе: сразу запишите строку в `fin_transactions`. В поле `source` укажите имя своего чата: `claude`, `kaspi-chat`, `sfk-chat` и т.д.
2. Перед записью проверьте дубль: если уже есть операция с той же датой, суммой и счётом, спросите, не одна ли это операция.
3. **Продажи Kaspi вручную не вносите.** Они подтягиваются автоматически через `fin_kaspi_monthly`. Вносите только реальные движения денег, которых нет в заказах: закуп, карго, реклама, налоги, вывод на карту, личные траты.
4. Перевод между своими счетами — это `type='transfer'` с `to_account_id`. Это не расход.
5. Если пользователь назвал текущий остаток счёта, обновите `opening_balance` и поставьте `opening_date = текущая дата`. Учтите операции, уже записанные на сегодня.
6. Никогда не храните полный номер карты, CVV, пароли и коды из SMS. Допустимы только последние 4 цифры.

Пример:
```sql
insert into public.fin_transactions (occurred_on, type, amount, account_id, project_id, category_id, note, source)
select current_date, 'expense', 12000,
  (select id from public.fin_accounts where slug = 'kaspi-gold'),
  (select id from public.fin_projects where slug = 'ads'),
  (select id from public.fin_categories where name = 'Реклама' and type = 'expense'),
  'таргет Instagram, подушки', 'claude';
```

## Как отвечать на вопросы о деньгах
- Сначала прочитайте свежие данные: `fin_account_balances`, `fin_transactions` за нужный период и `fin_kaspi_monthly`.
- Прибыль бизнеса за месяц считается так: выручка Kaspi − комиссия − себестоимость проданного + прочие доходы − расходы бизнес-проектов. «Закуп товара» в эту формулу не входит, потому что он уже учтён через себестоимость.
- Отвечайте цифрами и давайте конкретный совет: что сократить, где бюджет близок к лимиту, хватит ли денег до конца месяца, сколько приносит депозит.
