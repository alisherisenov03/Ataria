# 3D-модель подушки №1 (Blender)

Точная процедурная модель подушки «Бабочка» по фото `brand/ataria_pillow1_reference.jpg`
и студийная сцена в стиле Bork: тёплый тауп, подиум из травертина, мягкий ключевой свет.
Товар в кадре всегда одинаковый, в отличие от ИИ-генерации.

## Запуск
```bash
python3 -m venv bl && ./bl/bin/pip install bpy==5.2.3 scikit-image pillow
./bl/bin/python pillow_scene.py still hero.png hero    # виды: hero, front, top, macro
./bl/bin/python pillow_scene.py turn  out_dir 96       # облёт камеры, 96 кадров
ffmpeg -framerate 24 -i out_dir/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 turn.mp4
```
Рендер на процессоре (Cycles): кадр 1080×1350, 160 сэмплов, около 2–3 минут на 4 ядрах.

## Что настраивается в `pillow_scene.py`
- `outline_sdf`, `height`: контур сверху и высоты (крылья, валики, ямка под голову).
- `pillow_material`: серый бархат сверху и полосой по центру фасада, белая стёжка «ромб» по бокам.
- `build_scene`: подиум, фон, свет. `CAMERAS`: ракурсы.

## Дальше
Бирка ATARIA, макро стёжки, нажатие на пену, молния. Потом та же схема для AT-SM23.
