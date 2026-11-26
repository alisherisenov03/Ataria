import json
LOGO=open('logo.svg').read().split('?>',1)[1]
LG=LOGO.replace('<svg ','<svg style="height:100%;width:auto;display:block" ',1)
def logo(c,h): return f'<div style="color:{c};height:{h}px;display:flex">{LG}</div>'
F='<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter+Tight:wght@300;400;500;600&display=swap" rel="stylesheet">'
CSS=F+'''<style>*{margin:0;box-sizing:border-box}body{width:900px;height:900px;background:#17140F;font-family:"Inter Tight";font-variant-numeric:lining-nums;-webkit-font-smoothing:antialiased;color:#F4F1EC}
.lab{font-size:16px;letter-spacing:.3em;text-transform:uppercase;color:#D4B483;font-weight:500}
.tt{font-family:"Cormorant Garamond";font-weight:600;line-height:.98}
.g{display:grid;grid-template-columns:1fr 1fr;column-gap:34px;row-gap:16px}
.it{border-top:1px solid rgba(212,180,131,.45);padding-top:12px}
.it b{display:block;font-size:24px;font-weight:600;line-height:1.15}
.it span{display:block;font-size:18px;font-weight:300;color:#E2D9CC;line-height:1.35;margin-top:4px}
.ph{position:absolute;inset:0;width:900px;height:900px;object-fit:cover}
</style>'''
jobs=[]
def page(n,body):
    open(f'q_{n}.html','w').write(f'<!doctype html><meta charset="utf-8">{CSS}<body><div style="position:relative;width:900px;height:900px;overflow:hidden">{body}</div></body>'); jobs.append(n)
def slide(n,img,pos,kicker,title,items,grad=0.62,dark=.9):
    its=''.join(f'<div class="it"><b>{a}</b><span>{b}</span></div>' for a,b in items)
    page(n,f'''<img class="ph" src="{img}" style="object-position:{pos}">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(18,15,11,{dark}) 0%,rgba(18,15,11,{dark*0.85:.2f}) {int(grad*55)}%,rgba(18,15,11,0) {int(grad*100)}%)"></div>
<div style="position:absolute;left:50px;right:50px;top:44px;display:flex;justify-content:space-between;align-items:center"><div class="lab">{kicker}</div>{logo('#F4F1EC',20)}</div>
<div style="position:absolute;left:50px;right:50px;top:96px">
<div class="tt" style="font-size:70px">{title}</div>
<div class="g" style="margin-top:26px">{its}</div></div>''')
# hero
tiles=[('t_tools','Тестомес'),('t_bowl','Чаша 7 л'),('t_grind','Мясорубка'),('t_drums','Овощерезка'),('t_roll','Тесто и лапша'),('t_blend','Блендер')]
tl=''.join(f'<div style="width:128px;text-align:center"><img src="{f}.jpg" style="width:128px;height:128px;border-radius:14px;object-fit:cover;border:1px solid rgba(212,180,131,.5)"><div style="font-size:15px;font-weight:500;margin-top:7px">{t}</div></div>' for f,t in tiles)
specs=[('2000','Вт мощность'),('7 л','чаша из стали'),('1,5 л','стеклянный блендер'),('12','насадок')]
sp=''.join(f'<div style="margin-bottom:16px"><div class="tt" style="font-size:52px;color:#E9CF9F">{a}</div><div style="font-size:17px;font-weight:400;color:#E2D9CC;margin-top:2px">{b}</div></div>' for a,b in specs)
page('01',f'''<img class="ph" src="x_m06_low.jpg">
<div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(14,12,9,.92) 0%,rgba(14,12,9,.55) 30%,rgba(14,12,9,0) 50%),linear-gradient(180deg,rgba(14,12,9,.85) 0%,rgba(14,12,9,0) 26%,rgba(14,12,9,0) 66%,rgba(14,12,9,.95) 82%)"></div>
<div style="position:absolute;left:44px;top:40px">{logo('#F4F1EC',26)}</div>
<div style="position:absolute;left:44px;top:92px"><div class="tt" style="font-size:84px">Кухонная машина <span style="color:#E9CF9F">6 в 1</span></div></div>
<div style="position:absolute;left:44px;top:206px">{sp}</div>
<div style="position:absolute;left:24px;right:24px;bottom:22px;display:flex;justify-content:space-between">{tl}</div>''')
# contents
items=[('Тестомес','крюк, лопатка, венчик'),('Мясорубка','3 решётки + нож'),('Овощерезка','3 стальных барабана'),('Тестораскатка','8 положений толщины'),('Лапшерезка','ровная лапша для лагмана'),('Блендер','стеклянная колба 1,5 л')]
tiles2=[('t_tools','Тестомес','крюк, лопатка, венчик'),('t_grind','Мясорубка','3 решётки + нож'),('t_drums','Овощерезка','3 стальных барабана'),('t_roll','Тесто и лапша','8 толщин + лапшерезка'),('t_blend','Блендер','стекло, 1,5 л'),('t_bowl','Чаша 7 л','нержавеющая сталь')]
tg=''.join(f'<div><img src="{f}.jpg" style="width:250px;height:212px;object-fit:cover;border-radius:16px;border:1px solid rgba(212,180,131,.45)"><div style="font-size:24px;font-weight:600;margin-top:10px">{t}</div><div style="font-size:18px;font-weight:300;color:#E2D9CC;margin-top:2px">{d}</div></div>' for f,t,d in tiles2)
page('02',f'''<div style="position:absolute;inset:0;background:radial-gradient(120% 80% at 50% 0%,#2A241C 0%,#17140F 60%)"></div>
<div style="position:absolute;left:50px;right:50px;top:44px;display:flex;justify-content:space-between;align-items:center"><div class="lab">Комплектация</div>{logo('#F4F1EC',20)}</div>
<div style="position:absolute;left:50px;right:50px;top:96px"><div class="tt" style="font-size:70px">Один вместо <i>шести</i></div>
<div style="display:grid;grid-template-columns:repeat(3,250px);justify-content:space-between;row-gap:24px;margin-top:28px">{tg}</div></div>''')
slide('03','x_m02_open.jpg','50% 50%','Замес и взбивание','Планетарное <i>вращение</i>',
 [('Крюк — тесто','бешбармак, манты, баурсаки · скорость 1–2'),('Венчик — крем','безе, бисквит, сливки · 1–max'),('Лопатка — начинки','фарш, пюре, кремы · 1–max'),('Чаша 7 л','нерж. сталь, крышка от брызг')],grad=.62)
slide('04','x_m09_grinder.jpg','50% 50%','Мясорубка','Свежий фарш <i>дома</i>',
 [('3 решётки','мелкий, средний и крупный фарш'),('Стальной нож','крестовой, в комплекте'),('Насадки','для колбасок и кеббе'),('3 кг мяса','высокая производительность')],grad=.6)
slide('05','x_m10_slicer.jpg','50% 50%','Овощерезка','Салат <i>за минуту</i>',
 [('Мелкий нож','сыр, шоколад, овощи — стружка'),('Средний нож','овощи и фрукты соломкой'),('Нож-диск','ровные ломтики и кружочки'),('Цилиндр с толкателем','прозрачный, безопасный')],grad=.6)
slide('06','x_m11b_noodles.jpg','50% 50%','Тестораскатка и лапшерезка','Тесто и лапша <i>сами</i>',
 [('Тестораскатка','гладкие валики, 8 положений'),('Лапшерезка','зубчатые ножи, ровная лапша'),('Для чего','бешбармак, лагман, манты, лазанья'),('Боковой порт','ставится за секунды')],grad=.6)
slide('07','x_m12_blender.jpg','50% 50%','Блендер','Смузи <i>и пюре</i>',
 [('Колба 1,5 л','термостойкое стекло'),('Мерная шкала','точная дозировка'),('За секунды','смузи, пюре, соусы'),('Верхний порт','работает отдельно от чаши')],grad=.6)
slide('08','x_m01_front.jpg','50% 50%','Характеристики','Сделан, <i>чтобы служить</i>',
 [('Мощность 2000 Вт','справится с тугим тестом'),('6 скоростей + P','плавная регулировка ручкой'),('Таймер','дисплей, кнопки TIME + −'),('Гарантия до 2 лет','год + ещё год при регистрации')],grad=.6)
json.dump(jobs,open('jobs2.json','w'))
