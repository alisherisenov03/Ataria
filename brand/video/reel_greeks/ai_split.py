"""Cut re-cast (AI) group clips back into per-part clips for build.py's AI_DIR.

    python ai_split.py AI_DIR
AI_DIR holds src/srcNN.mp4 (from EXPORT_SRC), groups.json ({"g1": [0, 1, 2], ...}) and the
re-cast outputs out_g1.mp4, ...; writes aiNN.mp4. The model may return a slightly different
length, so each group is cut in proportion to its parts' source durations.
"""
import json
import subprocess
import sys
from pathlib import Path


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def main():
    root = Path(sys.argv[1])
    for group, parts in json.loads((root / "groups.json").read_text()).items():
        recast = root / f"out_{group}.mp4"
        if not recast.exists():
            print("missing", recast)
            continue
        src = [duration(root / "src" / f"src{i:02d}.mp4") for i in parts]
        scale = duration(recast) / sum(src)
        t = 0.0
        for i, d in zip(parts, src):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t * scale:.3f}", "-i", str(recast),
                            "-t", f"{d * scale:.3f}", "-an", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                            str(root / f"ai{i:02d}.mp4")], check=True)
            t += d


if __name__ == "__main__":
    main()
