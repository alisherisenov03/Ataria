# Автоматический разработчик (очередь задач Jarvis)

Раз в час запускается сессия Claude Code в этом репозитории. Она:

1. Читает задачи: `select id, title, description from jarvis.improvement_proposals where status = 'proposed' order by created_at` (Supabase, проект `pepexjsboutlqmqjyemc`).
2. Для каждой задачи, которую можно сделать по правилам ниже:
   - ставит `status = 'approved'` (взята в работу);
   - делает изменение в ветке `claude/ai-agent-audio-multiagent-qb4qz5`, прогоняет проверки (`backend/test_calc.py`, синтаксис), коммитит и пушит;
   - выкладывает бэкенд на Vercel (проект `jarvis-backend`, команда `team_GqKAboNJ4hAC2TOF0mc0T4BK`, target production, gitSource этой ветки) и ждёт `READY`, затем проверяет `GET /health`;
   - если менялся интерфейс окна: `npm run publish-ui` в `desktop/` и коммит `backend/static/app/`;
   - ставит `status = 'merged'` и пишет короткий итог для голоса в `jarvis.dev_log` (2–3 предложения, по-русски, без технических слов).
3. Задачу, которую нельзя сделать без Алишера, переводит в `rejected` с объяснением в `dev_log` («нужно ваше решение: …»).

## Нельзя без явного «да» Алишера
- удалять или массово менять данные (DROP/DELETE/TRUNCATE, изменения схемы `public`, сайт с промокодами);
- отправлять сообщения клиентам, креаторам, в Kaspi, WhatsApp, Instagram;
- тратить деньги, подключать платные сервисы, менять ключи и пароли;
- трогать проекты Railway `beautiful-ambition`, `passionate-manifestation` и Vercel-проекты `ataria`, `ataria-invest`.

## Если что-то сломалось
Откатить бэкенд: предыдущую сборку `jarvis-backend` с `READY` промоутить обратно (Vercel → Deployments → Promote / Rollback), записать в `dev_log`, что откачено и почему.
