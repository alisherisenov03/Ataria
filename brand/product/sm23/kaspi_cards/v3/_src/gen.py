G='#E8C068'
CSS=f'''<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{width:900px;height:900px;overflow:hidden;background:#000;font-family:Montserrat,sans-serif;color:#fff}}
.bg{{position:absolute;inset:0;width:900px;height:900px}}.a{{position:absolute}}
.h{{font-weight:900;text-transform:uppercase;line-height:.92;letter-spacing:-.5px;text-shadow:0 4px 24px rgba(0,0,0,.55)}}
.g{{color:{G}}}.t{{font-weight:600;text-shadow:0 2px 10px rgba(0,0,0,.7)}}
.plate{{background:rgba(14,13,12,.96);border:2px solid rgba(232,192,104,.75);border-radius:14px}}
.pill{{background:{G};color:#141210;font-weight:900;text-transform:uppercase;border-radius:40px;padding:10px 22px}}
</style>'''
def page(n,body): open(f's{n}.html','w').write(f'<html><head><meta charset="utf-8">{CSS}</head><body><img class="bg" src="c{n}.jpg">{body}</body></html>')
def stat(x,y,big,small,size=60):
    return f'<div class="a" style="left:{x}px;top:{y}px"><div class="h" style="font-size:{size}px">{big}</div><div class="t" style="font-size:19px;color:#ddd;margin-top:6px;text-transform:uppercase;letter-spacing:1px">{small}</div></div>'
# 1 hero
page(1,f'''<div class="a" style="left:0;top:560px;width:470px;height:340px;background:radial-gradient(ellipse at 0% 70%,rgba(0,0,0,.97) 45%,rgba(0,0,0,0) 75%)"></div>
<div class="a h" style="left:34px;top:34px;font-size:94px">Кухонный<br>комбайн</div>
<div class="a" style="left:36px;top:232px;font-size:27px;font-weight:800;letter-spacing:1px" ><span class="g">6 В 1</span> · ATARIA AT-SM23</div>
{stat(36,300,'2000 <span class="g">Вт</span>','мощность мотора')}
{stat(36,412,'7 <span class="g">л</span>','чаша из стали')}
{stat(36,524,'1,5 <span class="g">л</span>','стеклянный блендер')}
{stat(36,636,'12','насадок в комплекте')}
<div class="a pill" style="left:36px;top:800px;font-size:22px">Гарантия до 2 лет</div>''')
# 2 compare
rows=[('2000 Вт мощность','1500 Вт'),('Металл и стекло','Хлипкие детали'),('Тихая работа','Шумит, дребезжит'),('Двойная коробка','Мнётся в дороге'),('Честная цена','Переплата за бренд')]
r=''.join(f'''<div class="a" style="left:30px;top:{200+i*92}px;display:flex;align-items:center;gap:14px;font-size:29px;font-weight:800"><span style="width:38px;height:38px;border-radius:50%;background:#2DBE60;display:inline-flex;align-items:center;justify-content:center;font-size:24px">✓</span>{a}</div>
<div class="a" style="left:478px;top:{200+i*92}px;display:flex;align-items:center;gap:14px;font-size:27px;font-weight:600;color:#bbb"><span style="width:38px;height:38px;border-radius:50%;background:#D83A3A;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:22px">✕</span>{b}</div>''' for i,(a,b) in enumerate(rows))
page(2,f'''<div class="a h" style="left:0;width:900px;text-align:center;top:34px;font-size:76px">Почему <span class="g">ATARIA</span></div>
<div class="a" style="left:30px;top:138px;font-size:30px;font-weight:900;color:{G};letter-spacing:3px">ATARIA</div>
<div class="a" style="left:478px;top:138px;font-size:30px;font-weight:900;color:#888;letter-spacing:3px">ДРУГИЕ</div>
<div class="a" style="left:455px;top:140px;width:2px;height:560px;background:rgba(255,255,255,.18)"></div>{r}''')
# 3 display
page(3,f'''<div class="a" style="left:0;top:0;width:420px;height:420px;background:radial-gradient(ellipse at 0% 20%,rgba(0,0,0,.85) 30%,rgba(0,0,0,0) 72%)"></div>
<div class="a h" style="left:36px;top:110px;font-size:62px">Дисплей<br><span class="g">и таймер</span></div>
<div class="a t" style="left:38px;top:250px;font-size:22px;width:270px;line-height:1.3">Видно время даже в&nbsp;полутьме</div>
<div class="a plate" style="left:440px;top:362px;width:190px;padding:10px 0;text-align:center;font-weight:900;font-size:22px">TIME + −</div>
<div class="a" style="left:250px;top:478px;width:520px;height:150px;background:radial-gradient(ellipse at 50% 50%,rgba(0,0,0,.85) 40%,rgba(0,0,0,0) 72%)"></div>
<div class="a" style="left:250px;top:500px;width:520px;text-align:center"><div class="h" style="font-size:54px">До <span class="g">10 минут</span></div><div class="t" style="font-size:22px;margin-top:8px">отработает и выключится сам</div></div>''')
# 4 planetary
lab=lambda y,t:f'<div class="a plate" style="left:58px;top:{y}px;width:232px;padding:7px 0;text-align:center;font-weight:900;font-size:17px;text-transform:uppercase">{t}</div>'
page(4,f'''<div class="a" style="left:0;top:0;width:900px;height:300px;background:linear-gradient(180deg,rgba(0,0,0,.88) 0%,rgba(0,0,0,.6) 60%,rgba(0,0,0,0) 100%)"></div>
<div class="a h" style="left:30px;top:30px;font-size:64px">Планетарное<br><span class="g">вращение</span></div>
<div class="a t" style="left:32px;top:178px;font-size:22px;width:430px;line-height:1.3">Насадка обходит всю чашу — тесто без комков</div>
<div class="a" style="left:360px;top:232px;width:124px;height:124px;border-radius:50%;background:{G};color:#141210;display:flex;flex-direction:column;align-items:center;justify-content:center;box-shadow:0 6px 24px rgba(0,0,0,.5)"><div style="font-size:44px;font-weight:900;line-height:1">7 Л</div><div style="font-size:16px;font-weight:800">ЧАША</div></div>
{lab(452,'Крюк — тесто')}{lab(642,'Венчик — крем')}{lab(838,'Лопатка — фарш')}''')
# 5 slicer
pl=lambda y,t,d:f'<div class="a plate" style="left:158px;top:{y}px;width:312px;height:{122}px;background:#0e0d0c;padding:14px 16px"><div style="font-size:27px;font-weight:900;text-transform:uppercase;color:{G}">{t}</div><div style="font-size:18px;font-weight:600;margin-top:6px;line-height:1.25">{d}</div></div>'
page(5,f'''<div class="a" style="left:0;top:0;width:900px;height:160px;background:linear-gradient(180deg,rgba(0,0,0,.8),rgba(0,0,0,0))"></div>
<div class="a h" style="left:0;width:900px;text-align:center;top:24px;font-size:84px">Овощерезка</div>
{pl(140,'Мелкий нож','сыр, шоколад, чеснок — в стружку')}{pl(386,'Средний нож','овощи и фрукты соломкой')}{pl(626,'Нож-диск','ровные ломтики и кружочки')}''')
# 6 pasta
page(6,f'''<div class="a plate" style="left:652px;top:166px;width:244px;height:74px;padding:9px 12px;text-align:center"><div style="font-size:21px;font-weight:900;color:{G}">ТЕСТОРАСКАТКА</div><div style="font-size:16px;font-weight:600;margin-top:3px">8 толщин теста</div></div>
<div class="a plate" style="left:652px;top:366px;width:244px;height:74px;padding:9px 12px;text-align:center"><div style="font-size:21px;font-weight:900;color:{G}">ЛАПШЕРЕЗКА</div><div style="font-size:16px;font-weight:600;margin-top:3px">ровная лапша за минуты</div></div>
<div class="a" style="left:0;top:640px;width:900px;height:260px;background:linear-gradient(0deg,rgba(0,0,0,.92) 0%,rgba(0,0,0,.7) 45%,rgba(0,0,0,0) 100%)"></div>
<div class="a h" style="left:32px;top:770px;font-size:70px">Тесто <span class="g">и лапша</span></div>
<div class="a t" style="left:34px;top:846px;font-size:24px">домашние — для лагмана, бешбармака, пасты</div>''')
# 7 blender
ck=lambda y,t:f'<div class="a" style="left:34px;top:{y}px;display:flex;align-items:center;gap:14px;font-size:25px;font-weight:800"><span style="width:34px;height:34px;border-radius:50%;background:{G};color:#141210;display:inline-flex;align-items:center;justify-content:center;font-size:20px;font-weight:900">✓</span>{t}</div>'
page(7,f'''<div class="a h" style="left:30px;top:34px;font-size:96px">Блендер<br><span class="g">1,5 л</span></div>
{ck(262,'Жаропрочное стекло')}{ck(322,'Мерная шкала')}{ck(382,'Толкатель в комплекте')}
<div class="a plate" style="left:48px;top:530px;width:310px;height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:rgba(10,10,10,.98)"><div style="font-size:64px">🍓</div><div class="h" style="font-size:38px;margin-top:10px">Смузи<br>и пюре</div><div style="font-size:19px;font-weight:600;margin-top:12px;color:#ddd">однородно за секунды</div></div>''')
# 8 grinder
page(8,f'''<div class="a" style="left:0;top:0;width:620px;height:300px;background:radial-gradient(ellipse at 0% 0%,rgba(0,0,0,.92) 35%,rgba(0,0,0,0) 75%)"></div>
<div class="a h" style="left:30px;top:32px;font-size:70px">Мясорубка</div>
<div class="a h g" style="left:30px;top:106px;font-size:70px">3 кг мяса</div>
<div class="a t" style="left:32px;top:180px;font-size:22px;text-transform:uppercase;letter-spacing:1px">высокая производительность</div>
<div class="a t" style="left:40px;top:424px;width:250px;text-align:center;font-size:19px;font-weight:800;text-transform:uppercase;line-height:1.2">насадки для<br>колбасок и кеббе</div>
<div class="a" style="left:0;top:680px;width:330px;height:220px;background:radial-gradient(ellipse at 0% 50%,rgba(0,0,0,.85) 40%,rgba(0,0,0,0) 72%)"></div>
<div class="a h" style="left:30px;top:736px;font-size:36px"><span class="g">3 решётки</span><br><span style="font-size:27px">для фарша</span></div>
{''.join(f'<div class="a h" style="left:{x-110}px;width:220px;text-align:center;top:832px;font-size:30px">{t}</div>' for x,t in [(358,'мелкий'),(556,'крупный'),(756,'средний')])}''')
# 9 gift
page(9,f'''<div class="a" style="left:0;top:0;width:900px;height:260px;background:linear-gradient(180deg,rgba(0,0,0,.85),rgba(0,0,0,.55) 60%,rgba(0,0,0,0))"></div>
<div class="a h" style="left:0;width:900px;text-align:center;top:30px;font-size:70px">Лучший <span class="g">подарок</span></div>
<div class="a t" style="left:0;width:900px;text-align:center;top:112px;font-size:26px">маме, жене, на новоселье и свадьбу</div>
<div class="a pill" style="left:290px;top:160px;font-size:20px;width:320px;text-align:center">Фирменная коробка</div>''')
