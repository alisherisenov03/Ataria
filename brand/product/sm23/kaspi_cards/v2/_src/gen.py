import json,os
LOGO=open('logo.svg').read().split('?>',1)[1]
LG=LOGO.replace('<svg ','<svg style="height:100%;width:auto;display:block" ',1)
def logo(c,h): return f'<div style="color:{c};height:{h}px;display:flex">{LG}</div>'
F='<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter+Tight:wght@300;400;500&display=swap" rel="stylesheet">'
CSS=F+'''<style>*{margin:0;box-sizing:border-box}body{width:900px;height:900px;background:#17140F;font-family:"Inter Tight";font-variant-numeric:lining-nums;-webkit-font-smoothing:antialiased;color:#F4F1EC}
.lab{font-size:14px;letter-spacing:.32em;text-transform:uppercase;color:#C9A97A;font-weight:500}
.tt{font-family:"Cormorant Garamond";font-weight:500;line-height:1.02}
.bd{font-weight:300;font-size:18px;line-height:1.5;color:#D8CFC2}
.row{display:flex;gap:16px;padding:15px 0;border-top:1px solid rgba(201,169,122,.22)}
.row b{font-weight:500;color:#F4F1EC;font-size:20px;display:block}
.row span{font-weight:300;color:#B9AE9F;font-size:16px;line-height:1.4}
.n{font-family:"Cormorant Garamond";color:#C9A97A;font-size:24px;width:26px;flex:none;line-height:1}
</style>'''
jobs=[]
def page(name,body):
    open(f'p_{name}.html','w').write(f'<!doctype html><meta charset="utf-8">{CSS}<body><div style="position:relative;width:900px;height:900px;overflow:hidden">{body}</div></body>')
    jobs.append(name)
def split(name,img,pos,kicker,title,rows,lead=''):
    r=''.join(f'<div class="row"><div class="n">{i+1:02d}</div><div><b>{a}</b><span>{b}</span></div></div>' for i,(a,b) in enumerate(rows))
    body=f'''<img src="{img}" style="position:absolute;right:0;top:0;width:470px;height:900px;object-fit:cover;object-position:{pos}">
<div style="position:absolute;right:0;top:0;width:470px;height:900px;background:linear-gradient(90deg,#17140F 0%,rgba(23,20,15,0) 22%)"></div>
<div style="position:absolute;left:56px;top:56px">{logo('#F4F1EC',18)}</div>
<div style="position:absolute;left:56px;top:150px;width:390px">
<div class="lab">{kicker}</div>
<div class="tt" style="font-size:58px;margin-top:18px">{title}</div>
{f'<div class="bd" style="margin-top:18px">{lead}</div>' if lead else ''}
<div style="margin-top:30px">{r}</div></div>'''
    page(name,body)
# 1 hero
page('01',f'''<img src="ph/m06_low.jpg" style="position:absolute;inset:0;width:900px;height:900px;object-fit:cover;object-position:50% 0%">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,12,9,.9) 0%,rgba(14,12,9,.4) 26%,rgba(14,12,9,0) 40%,rgba(14,12,9,0) 80%,rgba(14,12,9,.8) 100%)"></div>
<div style="position:absolute;top:48px;left:0;right:0;display:flex;justify-content:center">{logo('#F4F1EC',24)}</div>
<div style="position:absolute;left:0;right:0;top:104px;text-align:center"><div class="lab">Кухонный комбайн</div><div class="tt" style="font-size:66px;margin-top:8px">6 в 1</div></div>
<div style="position:absolute;left:0;right:0;bottom:36px;display:flex;justify-content:center;gap:26px;font-size:17px;font-weight:400;letter-spacing:.06em;color:#E6DCCD">
<span>2000 Вт</span><span style="color:#C9A97A">·</span><span>Чаша 7 л</span><span style="color:#C9A97A">·</span><span>Блендер 1,5 л</span><span style="color:#C9A97A">·</span><span>12 насадок</span></div>''')
# 2 what's in the box
items=[('Тестомес','крюк, лопатка, венчик'),('Мясорубка','3 решётки и нож'),('Овощерезка','3 стальных барабана'),('Тестораскатка','8 положений толщины'),('Лапшерезка','ровная лапша'),('Блендер','стеклянная колба 1,5 л')]
cells=''.join(f'<div style="padding:16px 0;border-top:1px solid rgba(201,169,122,.22)"><b style="font-weight:500;font-size:20px">{a}</b><div style="font-weight:300;color:#B9AE9F;font-size:16px;margin-top:4px">{b}</div></div>' for a,b in items)
page('02',f'''<div style="position:absolute;left:0;top:0;width:900px;height:560px;background:url(ph_q1.jpg);background-size:900px auto;background-position:0 -670px"></div>
<div style="position:absolute;left:0;top:420px;width:900px;height:140px;background:linear-gradient(180deg,rgba(23,20,15,0),#17140F)"></div>
<div style="position:absolute;right:56px;bottom:44px">{logo('#F4F1EC',16)}</div>
<div style="position:absolute;left:56px;right:56px;top:545px">
<div style="display:flex;align-items:baseline;justify-content:space-between"><div class="tt" style="font-size:52px">Один вместо шести</div><div class="lab">Комплектация</div></div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;column-gap:36px;margin-top:20px">{cells}</div></div>''')
split('03','ph/m02_open.jpg','42% 50%','Замес и взбивание','Планетарное<br><i>вращение</i>',
 [('Крюк — тесто','бешбармак, манты, баурсаки · скорость 1–2'),('Венчик — крем','безе, бисквит, сливки · 1–max'),('Лопатка — начинки','фарш, пюре, кремы · 1–max'),('Чаша 7 л','нержавеющая сталь, крышка от брызг')],
 'Насадка вращается вокруг своей оси и по кругу чаши — тесто вымешивается равномерно.')
split('04','ph/m09_grinder.jpg','30% 50%','Мясорубка','Свежий фарш<br><i>дома</i>',
 [('3 решётки','мелкий, средний и крупный фарш'),('Стальной нож','острый крестовой нож в комплекте'),('Насадки','для колбасок и кеббе'),('3 кг мяса','высокая производительность')])
split('05','ph/m10_slicer.jpg','28% 50%','Овощерезка','Салат<br><i>за минуту</i>',
 [('Мелкий нож','сыр, шоколад, овощи — мелкая стружка'),('Средний нож','овощи и фрукты соломкой'),('Нож-диск','ровные ломтики и кружочки'),('Загрузочный цилиндр','с толкателем, прозрачный')])
split('06','ph/m11_sheet_roller.jpg','30% 50%','Тесто и лапша','Тонкое тесто<br><i>и лапша</i>',
 [('Тестораскатка','гладкие валики, 8 положений толщины'),('Лапшерезка','зубчатые ножи, ровная лапша'),('Для чего','бешбармак, лагман, манты, лазанья'),('Боковой порт','насадки ставятся за секунды')])
split('07','ph/m12_blender.jpg','55% 50%','Блендер','Смузи<br><i>и пюре</i>',
 [('Колба 1,5 л','прочное термостойкое стекло'),('Мерная шкала','точная дозировка'),('Однородная масса','смузи, пюре, соусы за секунды'),('Верхний порт','блендер работает отдельно от чаши')])
specs=[('Мощность','2000 Вт'),('Чаша','7 л, нержавеющая сталь'),('Блендер','1,5 л, стекло'),('Скорости','6 + импульс P'),('Таймер','дисплей, TIME + −'),('Насадок','12'),('Цвет','тёмный титан'),('Гарантия','до 2 лет')]
srows=''.join(f'<div style="display:flex;justify-content:space-between;padding:12px 0;border-top:1px solid rgba(201,169,122,.22);font-size:18px"><span style="color:#B9AE9F;font-weight:300">{a}</span><span style="font-weight:500">{b}</span></div>' for a,b in specs)
page('08',f'''<img src="ph/m07_display.jpg" style="position:absolute;right:0;top:0;width:430px;height:900px;object-fit:cover;object-position:50% 50%">
<div style="position:absolute;right:0;top:0;width:430px;height:900px;background:linear-gradient(90deg,#17140F 0%,rgba(23,20,15,0) 22%)"></div>
<div style="position:absolute;left:56px;top:56px">{logo('#F4F1EC',18)}</div>
<div style="position:absolute;left:56px;top:150px;width:410px">
<div class="lab">Характеристики</div>
<div class="tt" style="font-size:54px;margin-top:18px">Сделан,<br><i>чтобы служить</i></div>
<div style="margin-top:26px">{srows}</div>
<div class="bd" style="margin-top:18px;font-size:14px;color:#B9AE9F">Год гарантии + ещё год при регистрации в WhatsApp.</div></div>''')
json.dump(jobs,open('jobs.json','w'))
