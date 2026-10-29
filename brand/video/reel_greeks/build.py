"""Reel «На чём спали древние греки» — vertical 1080x1920 montage of the owner's footage.

Layout: title + illustration on top, the horizontal footage in the middle, captions below.
Audio: the owner's own voice, cleaned (rumble cut, denoise, compression, loudness).
    python build.py RAW_DIR IMG_DIR OUT_DIR
RAW_DIR holds v1..v4.mp4, IMG_DIR the illustrations named in EDL.
"""
import json
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
VID_Y, VID_H = 1060, 602          # 832x464 source scaled to full width
IMG_Y, IMG_SIZE = 300, 720
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
CAP_FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
BG = "0x16130f"

# segments: (title, illustration, [(video, in, out, caption), ...])
EDL = [
    ("НА ЧЁМ СПАЛИ\nДРЕВНИЕ ГРЕКИ?", "greek.png", [
        (1, 3.05, 7.75, "Вот как спали древние греки, у которых были вот такие лица"),
        (1, 10.7, 13.75, "Это помогало им держать голову прямо"),
        (1, 15.3, 17.8, "и не перегружать шею"),
    ]),
    ("ОБЫЧНАЯ ПОДУШКА", "posture.png", [
        (1, 41.25, 46.85, "А вот так мы спим на обычных подушках: голове не на что опереться"),
    ]),
    ("НА БОКУ ШЕЯ\nПРОГИБАЕТСЯ", "neck_flat.png", [
        (2, 8.6, 11.95, "Сбоку нет поддержки, голова проваливается"),
        (2, 12.55, 16.1, "и шея всю ночь прогибается"),
        (2, 17.5, 20.1, "отсюда и боли в шее"),
    ]),
    ("ATARIA:\nШЕЯ ЛЕЖИТ РОВНО", "neck_ataria.png", [
        (1, 138.95, 147.85, "Это ортопедическая подушка: полная поддержка шеи, голова прямо, шея расслаблена"),
    ]),
    ("НА БОКУ —\nТОЖЕ РОВНО", "neck_ataria.png", [
        (2, 38.45, 42.6, "Здесь нет провалов, шея плотно лежит на подушке"),
        (2, 46.75, 48.3, "и держится ровно"),
    ]),
    ("НА СПИНЕ · НА БОКУ\nНА ЖИВОТЕ", "hero.jpg", [
        (3, 8.8, 10.7, "Можно спать вот так"),
        (3, 20.8, 23.2, "и вот так"),
        (3, 48.9, 51.6, "а на животе — руки сюда"),
    ]),
    ("ЧЕХОЛ СНИМАЕТСЯ\nИ СТИРАЕТСЯ", "macro.jpg", [
        (4, 53.55, 55.9, "Наволочку можно снимать и стирать"),
        (4, 67.65, 69.0, "В комплекте"),
        (4, 71.75, 74.3, "шёлковая наволочка, вот она"),
    ]),
    ("НАПИШИ «ШЕЯ» —\nПРИШЛЮ ПРОМОКОД", "hero.jpg", [
        (4, 80.5, 83.3, "Пишите в WhatsApp или заказывайте на Kaspi"),
    ]),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def chunks(text, n=4):
    words = text.split()
    return [" ".join(words[i:i + n]) for i in range(0, len(words), n)]


def build_part(raw, img_dir, tmp, idx, sub, title, image):
    v, a, b, caption = sub
    dur = b - a
    out = tmp / f"part{idx:02d}.mp4"
    # captions: 4-word chunks spread evenly over the clip
    parts = chunks(caption)
    step = dur / len(parts)
    cap_filters = []
    for k, text in enumerate(parts):
        cap_filters.append(
            f"drawtext=fontfile='{CAP_FONT}':text='{esc(text)}':fontsize=60:fontcolor=white:"
            f"box=1:boxcolor=black@0.55:boxborderw=18:x=(w-text_w)/2:y={VID_Y + VID_H + 70}:"
            f"enable='between(t,{k * step:.3f},{(k + 1) * step:.3f})'"
        )
    title_lines = title.split("\n")
    title_filters = [
        f"drawtext=fontfile='{FONT}':text='{esc(line)}':fontsize=78:fontcolor=0xf3ede4:"
        f"x=(w-text_w)/2:y={70 + i * 96}"
        for i, line in enumerate(title_lines)
    ]
    graph = (
        f"color=c={BG}:s={W}x{H}:d={dur:.3f}:r=30[bg];"
        f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30,scale={W}:{VID_H},eq=contrast=1.06:saturation=1.08[vid];"
        f"[1:v]scale={IMG_SIZE}:{IMG_SIZE}:force_original_aspect_ratio=increase,crop={IMG_SIZE}:{IMG_SIZE}[img];"
        f"[bg][img]overlay=(W-w)/2:{IMG_Y}[b1];"
        f"[b1][vid]overlay=0:{VID_Y}[b2];"
        f"[b2]{','.join(title_filters + cap_filters)}[outv];"
        f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,highpass=f=90,lowpass=f=12000,afftdn=nf=-25,"
        f"acompressor=threshold=-20dB:ratio=3:attack=5:release=120,afade=t=in:d=0.04,"
        f"afade=t=out:st={dur - 0.06:.3f}:d=0.06,aresample=48000[outa]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw / f"v{v}.mp4"), "-loop", "1", "-t", f"{dur:.3f}",
         "-i", str(img_dir / image), "-filter_complex", graph, "-map", "[outv]", "-map", "[outa]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(out)])
    return out


def main():
    raw, img_dir, out_dir = map(Path, sys.argv[1:4])
    tmp = out_dir / "parts"
    tmp.mkdir(parents=True, exist_ok=True)
    parts, idx = [], 0
    for title, image, subs in EDL:
        for sub in subs:
            parts.append(build_part(raw, img_dir, tmp, idx, sub, title, image))
            idx += 1
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    joined = out_dir / "joined.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    final = out_dir / "reel_greeks_draft.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
    total = sum(b - a for _, _, subs in EDL for _, a, b, _ in subs)
    print(json.dumps({"parts": len(parts), "seconds": round(total, 1), "out": str(final)}))


if __name__ == "__main__":
    main()
