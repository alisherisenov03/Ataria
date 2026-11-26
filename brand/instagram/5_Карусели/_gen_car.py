import json,os,re
src=open('gen.py').read()
exec(src.split('# ---------- Reels')[0])   # CSS, logo, page, jobs
CSS2=CSS.replace('family=Cormorant','family=Montserrat:wght@600;700;800;900&family=Cormorant')
globals()['CSS']=CSS2
G='#E8C068'
SH='text-shadow:0 4px 28px rgba(0,0,0,.6)'
def grad(where):
    return ('linear-gradient(0deg,rgba(12,11,10,.92) 0%,rgba(12,11,10,.75) 28%,rgba(12,11,10,0) 55%)' if where=='b'
            else 'linear-gradient(180deg,rgba(12,11,10,.9) 0%,rgba(12,11,10,.7) 26%,rgba(12,11,10,0) 52%)')
def car_cover(name,ph,kicker,title,sub,out,pos='50% 50%'):
    body=f'''<img class="ph" src="photos/{ph}.jpg" style="object-position:{pos}"><div style="position:absolute;inset:0;background:{grad('b')}"></div>
<div style="position:absolute;top:64px;left:70px">{logo('#fff',30)}</div>
<div style="position:absolute;left:70px;right:70px;bottom:80px;color:#fff;font-family:Montserrat;{SH}">
<div style="font-weight:800;font-size:30px;letter-spacing:.14em;text-transform:uppercase;color:{G}">{kicker}</div>
<div style="font-weight:900;font-size:122px;line-height:.92;text-transform:uppercase;margin-top:18px;letter-spacing:-1px">{title}</div>
<div style="display:flex;justify-content:space-between;align-items:end;margin-top:28px;font-size:34px;font-weight:700"><span>{sub}</span><span style="font-size:26px;font-weight:800;letter-spacing:.14em;color:{G}">ЛИСТАЙТЕ →</span></div></div>'''
    page(name,1080,1350,body,out)
def car_slide(name,ph,n,total,title,text,out,where='b',pos='50% 50%'):
    box=('bottom:80px' if where=='b' else 'top:150px')
    body=f'''<img class="ph" src="photos/{ph}.jpg" style="object-position:{pos}"><div style="position:absolute;inset:0;background:{grad(where)}"></div>
<div style="position:absolute;top:64px;left:70px;right:70px;display:flex;justify-content:space-between;align-items:center;font-family:Montserrat;font-weight:800;font-size:30px;color:{G};{SH}">{logo('#fff',26)}<span>{n:02d} / {total:02d}</span></div>
<div style="position:absolute;left:70px;right:70px;{box};color:#fff;font-family:Montserrat;{SH}">
<div style="font-weight:900;font-size:96px;line-height:.95;text-transform:uppercase;letter-spacing:-1px">{title}</div>
<div style="font-weight:700;font-size:38px;line-height:1.3;margin-top:22px;max-width:900px">{text}</div></div>'''
    page(name,1080,1350,body,out)
def car_cta(name,out,h=1350,ph='m06_low'):
    body=f'''<img class="ph" src="photos/{ph}.jpg"><div style="position:absolute;inset:0;background:rgba(12,11,10,.72)"></div>
<div style="position:absolute;top:300px;left:0;right:0;display:flex;justify-content:center">{logo('#fff',64)}</div>
<div style="position:absolute;top:420px;left:0;right:0;text-align:center;font-family:Montserrat;font-weight:900;font-size:76px;line-height:1;color:#fff;text-transform:uppercase">Кухонный<br>комбайн <span style="color:{G}">6 в 1</span></div>
<div style="position:absolute;left:150px;right:150px;top:690px;font-family:Montserrat;font-weight:800;font-size:44px;text-align:center;color:#fff">
<div style="background:{G};color:#141210;border-radius:60px;padding:22px 0">Kaspi · рассрочка</div>
<div style="border:3px solid {G};border-radius:60px;padding:19px 0;margin-top:26px">До 2 лет гарантии</div>
<div style="border:3px solid {G};border-radius:60px;padding:19px 0;margin-top:26px">Ссылка в профиле</div></div>'''
    page(name,1080,h,body,out)
c1=[('m02_open','Тестомес','Месит тесто для бешбармака, мантов и баурсаков сам.','b'),
('m09_grinder','Мясорубка','Свежий фарш для мантов и котлет. Ставится за секунды.','t'),
('m10_slicer','Овощерезка','Нарезка и тёрка. 3 стальных барабана.','t'),
('m11_sheet_roller','Тестораскатка','Ровный тонкий лист. 8 положений толщины.','t'),
('m11b_noodles','Лапшерезка','Лапша для лагмана — без скалки и ножа.','t'),
('m12_blender','Блендер','Стекло 1,5 л: смузи, соусы, супы-пюре.','t')]
car_cover('c1_00','m01_front','Один вместо шести','6 в 1','2000 Вт · чаша 7 л','5_Карусели/1_Карусель_6_в_1/01_cover.png')
for i,(ph,t,tx,w) in enumerate(c1,1): car_slide(f'c1_{i:02d}',ph,i,6,t,tx,f'5_Карусели/1_Карусель_6_в_1/{i+1:02d}_{ph}.png',w)
car_cta('c1_cta','5_Карусели/1_Карусель_6_в_1/08_cta.png')
c2=[('m07_display','Таймер на корпусе','Синие цифры, кнопки TIME + −. Подсказки скоростей прямо над ними.','b'),
('m02_open','Голова поднимается','Насадки меняются за секунды, чашу легко снять.','b'),
('m08_attachments','Металл, не пластик','Крюк, лопатка и венчик — литой металл и сталь.','b'),
('m04_back','Красив со всех сторон','Матовый титаново-серый корпус — сзади так же чисто.','t'),
('m05_top','Чаша 7 литров','Тесто на большую семью и гостей.','b')]
car_cover('c2_00','m06_low','Детали','Сделан,<br>чтобы стоять<br>на виду','Матовый титановый корпус','5_Карусели/2_Карусель_Детали/01_cover.png')
for i,(ph,t,tx,w) in enumerate(c2,1): car_slide(f'c2_{i:02d}',ph,i,5,t,tx,f'5_Карусели/2_Карусель_Детали/{i+1:02d}_{ph}.png',w)
car_cta('c2_cta','5_Карусели/2_Карусель_Детали/07_cta.png')
json.dump(jobs,open('jobs.json','w'),indent=0); print(len(jobs))
