"""Reel «На чём спали древние греки» — vertical 1080x1920 montage of the owner's footage.

Layout: title + illustration on top, the horizontal footage in the middle, captions below.
Audio: the owner's own voice, cleaned (rumble cut, denoise, compression, loudness);
pauses inside phrases are cut and the whole reel runs at SPEED.
    python build.py RAW_DIR IMG_DIR OUT_DIR
RAW_DIR holds v1..v4.mp4, IMG_DIR the illustrations named in EDL.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
VID_Y, VID_H = 700, 900           # the person is the main thing: 832x464 source scaled up, sides cropped
IMG_Y, IMG_SIZE = 270, 400        # small product card between title and footage
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
CAP_FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
BG = "0x16130f"

SPEED = 1.12        # whole reel slightly faster
PAD, GAP = 0.12, 0.3  # keep this much around speech; pauses longer than GAP are cut
EXPORT_SRC = os.environ.get("EXPORT_SRC")  # dir: also write each part's raw footage (for the AI re-cast)
AI_DIR = os.environ.get("AI_DIR")          # dir with aiNN.mp4: use re-cast footage instead of the source video

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
    ("ATARIA:\nШЕЯ ЛЕЖИТ РОВНО", "info_profile.png", [
        (1, 138.95, 147.85, "Это ортопедическая подушка: полная поддержка шеи, голова прямо, шея расслаблена"),
    ]),
    ("НА БОКУ —\nТОЖЕ РОВНО", "info_top.png", [
        (2, 38.45, 42.6, "Здесь нет провалов, шея плотно лежит на подушке"),
        (2, 46.75, 48.3, "и держится ровно"),
    ]),
    ("МОЖНО СПАТЬ\nНА СПИНЕ", "photo_bed.png", [
        (3, 8.9, 11.4, "На ортопедической подушке можно спать вот так"),
    ]),
    ("НА БОКУ\nИ НА ЖИВОТЕ", "photo_top.png", [
        (3, 20.85, 21.7, "А также можно спать"),
        (3, 26.9, 27.9, "вот так"),
        (3, 28.2, 29.9, "просунув сюда руки"),
        (3, 54.9, 56.5, "и можно расслабленно спать"),
    ]),
    ("ВЫЕМКА —\nЧТОБЫ ДЫШАТЬ", "photo_foam.png", [
        (3, 57.3, 60.4, "А эта выемка — чтобы можно было дышать"),
    ]),
    ("ЧЕХОЛ СНИМАЕТСЯ\nИ СТИРАЕТСЯ", "info_zip.png", [
        (4, 52.85, 55.8, "Наволочку можно снимать и стирать"),
        (4, 57.6, 58.85, "она легко снимается"),
    ]),
    ("+ ШЁЛКОВАЯ\nНАВОЛОЧКА", "photo_silk.png", [
        (4, 67.7, 69.0, "В комплекте также"),
        (4, 71.65, 74.2, "шёлковая наволочка — вот она"),
    ]),
    ("НА KASPI —\n600 ОТЗЫВОВ · 4,9", "kaspi.png", [
        (4, 37.85, 46.0, "Заказать можно на Kaspi: уже 600 отзывов и рейтинг 4,9"),
    ]),
    ("НАПИШИ «ШЕЯ» —\nПРИШЛЮ ПРОМОКОД", "photo_bed_two.png", [
        (4, 80.5, 83.3, "Пишите в WhatsApp или заказывайте на Kaspi"),
    ]),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def esc(text):
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def chunks(text, limit=24):
    """Greedy word chunks that fit the frame width at the caption size."""
    out = []
    for word in text.split():
        if out and len(out[-1]) + 1 + len(word) <= limit:
            out[-1] += " " + word
        else:
            out.append(word)
    return out


def speech(path, cache={}):
    """Speech intervals of a source, from ffmpeg silencedetect."""
    if path not in cache:
        log = subprocess.run(["ffmpeg", "-i", str(path), "-vn", "-af", "highpass=f=120,silencedetect=n=-32dB:d=0.35",
                              "-f", "null", "-"], capture_output=True, text=True).stderr
        starts = [float(l.split("silence_start: ")[1]) for l in log.splitlines() if "silence_start: " in l]
        ends = [float(l.split("silence_end: ")[1].split()[0]) for l in log.splitlines() if "silence_end: " in l]
        bounds, t = [], 0.0
        for a, b in zip(starts, ends + [1e9] * (len(starts) - len(ends))):
            if a > t:
                bounds.append((t, a))
            t = b
        bounds.append((t, 1e9))
        cache[path] = bounds
    return cache[path]


def keep_ranges(path, a, b):
    """Parts of [a, b] around speech: long pauses inside a phrase are cut out."""
    out = []
    for s0, s1 in speech(path):
        lo, hi = max(a, s0 - PAD), min(b, s1 + PAD)
        if hi - lo < 0.05:
            continue
        if out and lo - out[-1][1] < GAP:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out or [(a, b)]


def build_part(raw, img_dir, tmp, idx, sub, title, image):
    v, a, b, caption = sub
    src = raw / f"v{v}.mp4"
    ranges = keep_ranges(src, a, b)
    dur = sum(hi - lo for lo, hi in ranges) / SPEED
    sel = "+".join(f"between(t,{lo:.3f},{hi:.3f})" for lo, hi in ranges)
    out = tmp / f"part{idx:02d}.mp4"
    if EXPORT_SRC:
        Path(EXPORT_SRC).mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-an", "-vf", f"fps=30,select='{sel}',setpts=N/30/TB",
             "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(Path(EXPORT_SRC) / f"src{idx:02d}.mp4")])
    ai = Path(AI_DIR) / f"ai{idx:02d}.mp4" if AI_DIR else None
    if ai and ai.exists():
        ai_dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                       str(ai)], capture_output=True, text=True).stdout)
        vid_in = f"[2:v]setpts=PTS*{dur / ai_dur:.5f},fps=30,"
    else:
        ai, vid_in = None, f"[0:v]fps=30,select='{sel}',setpts=N/30/{SPEED}/TB,fps=30,"
    # captions: short chunks spread over the clip by length
    parts = chunks(caption)
    weights = [len(t) + 4 for t in parts]
    marks = [dur * sum(weights[:k]) / sum(weights) for k in range(len(parts) + 1)]
    cap_filters = []
    for k, text in enumerate(parts):
        cap_filters.append(
            f"drawtext=fontfile='{CAP_FONT}':text='{esc(text)}':fontsize=60:fontcolor=white:"
            f"box=1:boxcolor=black@0.55:boxborderw=18:x=(w-text_w)/2:y={VID_Y + VID_H - 150}:"
            f"enable='between(t,{marks[k]:.3f},{marks[k + 1]:.3f})'"
        )
    title_lines = title.split("\n")
    title_filters = [
        f"drawtext=fontfile='{FONT}':text='{esc(line)}':fontsize=78:fontcolor=0xf3ede4:"
        f"x=(w-text_w)/2:y={70 + i * 96}"
        for i, line in enumerate(title_lines)
    ]
    graph = (
        f"color=c={BG}:s={W}x{H}:d={dur:.3f}:r=30[bg];"
        f"{vid_in}scale=-2:{VID_H}:flags=lanczos,crop={W}:{VID_H},eq=contrast=1.06:saturation=1.08[vid];"
        f"[1:v]scale={IMG_SIZE}:{IMG_SIZE}:force_original_aspect_ratio=increase,crop={IMG_SIZE}:{IMG_SIZE}[img];"
        f"[bg][img]overlay=(W-w)/2:{IMG_Y}[b1];"
        f"[b1][vid]overlay=0:{VID_Y}:eof_action=repeat[b2];"
        f"[b2]{','.join(title_filters + cap_filters)}[outv];"
        f"[0:a]aselect='{sel}',asetpts=N/SR/TB,atempo={SPEED},highpass=f=90,lowpass=f=12000,afftdn=nf=-25,"
        f"acompressor=threshold=-20dB:ratio=3:attack=5:release=120,afade=t=in:d=0.04,"
        f"afade=t=out:st={dur - 0.06:.3f}:d=0.06,aresample=48000[outa]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-loop", "1", "-t", f"{dur:.3f}",
         "-i", str(img_dir / image), *(["-i", str(ai)] if ai else []), "-filter_complex", graph, "-map", "[outv]", "-map", "[outa]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(out)])
    return out, dur


def main():
    raw, img_dir, out_dir = map(Path, sys.argv[1:4])
    tmp = out_dir / "parts"
    tmp.mkdir(parents=True, exist_ok=True)
    parts, idx = [], 0
    for title, image, subs in EDL:
        for sub in subs:
            parts.append(build_part(raw, img_dir, tmp, idx, sub, title, image))
            idx += 1
    total = sum(d for _, d in parts)
    parts = [p for p, _ in parts]
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    joined = out_dir / "joined.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    final = out_dir / "reel_greeks_ai.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-c:v", "copy",
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)])
    print(json.dumps({"parts": len(parts), "seconds": round(total, 1), "out": str(final)}))


if __name__ == "__main__":
    main()
