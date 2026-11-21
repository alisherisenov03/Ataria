import csv, datetime as dt, collections, sys
rows=list(csv.DictReader(open(sys.argv[1],encoding='utf-8'),delimiter=';'))
P=['Алишер','Жена']
def fmt(x): return f"{x:,.0f}".replace(',',' ')+' ₸'
def share(r):
    a=float(r['amount_kzt']); s=r['payer_split']
    return {'Алишер':a,'Жена':0} if s=='alisher' else {'Алишер':0,'Жена':a} if s=='wife' else {'Алишер':a/2,'Жена':a/2}
day=collections.defaultdict(lambda:{p:0 for p in P}); cat=collections.defaultdict(lambda:{p:0 for p in P})
for r in rows:
    sh=share(r); n=int(r['nights']); d0=dt.date.fromisoformat(r['date'])
    for p in P: cat[r['category']][p]+=sh[p]
    days=[d0+dt.timedelta(i) for i in range(n)] if n else [d0]
    for d in days:
        for p in P: day[d][p]+=sh[p]/len(days)
o=["# Поездка в Китай, ноябрь 2026 — учёт расходов","",
"Маршрут: Астана → Гуанчжоу → Чжуншань → Нинбо → Юйяо → Шанхай → Астана","Участники: Алишер и жена","",
"## Правила расчёта",
"- **Отели** — целиком на Алишера (номер всё равно был бы оплачен одним человеком).",
"- **Перелёты, поезда** — по билету каждого; если билет на двоих — пополам.",
"- **Такси** — целиком на Алишера.",
"- **Еда** — целиком на Алишера, норма 10 000 ₸ в день в Китае.",
"- **Прочее общее** — пополам, если не указано иное.",
"- **Назначение**: бизнес (поездка к поставщикам) / личное (отдых).",
"- Отели по дням — стоимость делится на ночи; остальное — на дату поездки/траты.",
"- Источник данных: `expenses.csv`; этот файл генерируется `python3 build.py expenses.csv > expenses.md`.","",
"## Все расходы","","| # | Дата | Город | Категория | Назначение | Что | Сумма | Алишер | Жена | Бронь | Примечание |","|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    sh=share(r); d=dt.date.fromisoformat(r['date']).strftime('%d.%m')
    o.append(f"| {r['id']} | {d} | {r['city']} | {r['category']} | {r['purpose']} | {r['item']} | {fmt(float(r['amount_kzt']))} | {fmt(sh['Алишер'])} | {fmt(sh['Жена'])} | {r['booking']} | {r['note']} |")
T={p:sum(c[p] for c in cat.values()) for p in P}
o+=["","## По категориям","","| Категория | Алишер | Жена | Всего |","|---|---|---|---|"]
for k,v in sorted(cat.items(),key=lambda kv:-sum(kv[1].values())):
    o.append(f"| {k} | {fmt(v['Алишер'])} | {fmt(v['Жена'])} | {fmt(sum(v.values()))} |")
o.append(f"| **Итого** | **{fmt(T['Алишер'])}** | **{fmt(T['Жена'])}** | **{fmt(sum(T.values()))}** |")
o+=["","## По дням","","| День | Алишер | Жена | Всего |","|---|---|---|---|"]
for d in sorted(day):
    v=day[d]; o.append(f"| {d.strftime('%d.%m')} | {fmt(v['Алишер'])} | {fmt(v['Жена'])} | {fmt(sum(v.values()))} |")
o.append(f"| **Итого** | **{fmt(T['Алишер'])}** | **{fmt(T['Жена'])}** | **{fmt(sum(T.values()))}** |")
pur=collections.defaultdict(lambda:{p:0 for p in P})
for r in rows:
    sh=share(r)
    for p in P: pur[r['purpose']][p]+=sh[p]
o+=["","## Бизнес / личное","","| Назначение | Алишер | Жена | Всего |","|---|---|---|---|"]
for k,v in pur.items(): o.append(f"| {k} | {fmt(v['Алишер'])} | {fmt(v['Жена'])} | {fmt(sum(v.values()))} |")
print('\n'.join(o))
