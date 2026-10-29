# WhatsApp-бот ATARIA: подключение

Бот уже выложен: `https://pepexjsboutlqmqjyemc.supabase.co/functions/v1/whatsapp-bot`
(Supabase, проект сайта с промокодами). Он молчит, пока не заполнены 6 секретов ниже.

Номер бота: +7 700 110 4970. Подключаем через официальный WhatsApp Cloud API от Meta,
без посредников: абонплаты нет, ответы клиенту в течение 24 часов после его сообщения бесплатны.

## 1. Номер
Если на +7 700 110 4970 уже стоит WhatsApp в телефоне, его нужно удалить:
WhatsApp → Настройки → Аккаунт → Удалить аккаунт. Иначе Meta не даст подключить номер к API.
SIM-карта должна быть под рукой: придёт SMS с кодом.

## 2. Приложение Meta
1. developers.facebook.com → My Apps → Create app → тип **Business** → привязать к бизнес-аккаунту ATARIA.
2. В приложении добавить продукт **WhatsApp**.
3. WhatsApp → API Setup → **Add phone number**: имя ATARIA, категория «Shopping and retail», номер +7 700 110 4970, код из SMS.
4. Скопировать **Phone number ID** → это `WA_PHONE_NUMBER_ID`.
5. App settings → Basic → **App secret** → это `WA_APP_SECRET`.
6. business.facebook.com → Настройки → Пользователи → **Системные пользователи** → Добавить (роль Admin)
   → Назначить ресурсы: приложение и WhatsApp-аккаунт, полный доступ
   → **Создать токен**: разрешения `whatsapp_business_messaging` и `whatsapp_business_management`, срок «Никогда» → это `WA_TOKEN`.

## 3. Ключ Claude
console.anthropic.com → Settings → API keys → Create key → это `ANTHROPIC_API_KEY`.
В Billing пополнить баланс на 10–20 $. Одна переписка с клиентом обходится примерно в несколько центов.

## 4. Секреты в Supabase
supabase.com → проект → Edge Functions → **Secrets** → добавить:

| Имя | Значение |
|---|---|
| `ANTHROPIC_API_KEY` | ключ из шага 3 |
| `WA_TOKEN` | токен системного пользователя |
| `WA_PHONE_NUMBER_ID` | Phone number ID |
| `WA_APP_SECRET` | App secret |
| `WA_VERIFY_TOKEN` | любое придуманное слово, например `ataria-2026-sleep` |
| `OWNER_PHONE` | ваш личный номер цифрами, например `7701XXXXXXX` |

Ключи и токены никому не пересылайте, в том числе в чат. Они вводятся только в Supabase.

## 5. Webhook
developers.facebook.com → приложение → WhatsApp → **Configuration** → Webhook → Edit:
- Callback URL: `https://pepexjsboutlqmqjyemc.supabase.co/functions/v1/whatsapp-bot`
- Verify token: то же слово, что в `WA_VERIFY_TOKEN`
- Verify and save → в Webhook fields подписаться на **messages**.

Затем перевести приложение в режим **Live** (нужна ссылка на политику конфиденциальности, её добавим на сайт).

## 6. Проверка
Напишите боту со своего телефона «Здравствуйте, какую подушку посоветуете?».

## Как работает
- Отвечает на языке клиента, советует подушку, проверяет промокод, оформляет заказ и считает сумму по ценам из базы сайта.
- Отправляет ссылку Kaspi Pay и просит чек. Когда приходит фото чека, пишет вам.
- Жалобы, брак, «позовите человека» — сразу пишет вам.
- Вся переписка и заказы лежат в Supabase: таблицы `wa_messages`, `wa_orders`, `wa_handoffs`.

## Ограничения
- Уведомления владельцу приходят обычным сообщением от бота, а WhatsApp разрешает их только в течение 24 часов после вашего последнего сообщения боту.
  Пока не одобрен шаблон уведомлений, напишите боту что-нибудь утром, и весь день уведомления будут доходить.
- Поступление денег бот сам не видит: открытого API у Kaspi Pay для этого нет. Оплату по чеку проверяете вы в приложении Kaspi Pay.
