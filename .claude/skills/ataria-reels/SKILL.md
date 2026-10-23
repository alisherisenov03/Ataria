---
name: ataria-reels
description: Produce an Instagram/TikTok reel for an Ataria product from idea to rendered MP4: trend check, storyboard, frames in Higgsfield, design check, montage in HyperFrames. Use when Alisher asks for a reel, video, content plan, or "сделай ролик".
---

# Ataria reels

## 1. Formula (vidIQ trend research, Oct 2026, Russian-speaking KZ/CIS, women 25-45)
Finished dish in the first 3 seconds, big on-screen text, fast top-down cuts, upbeat music, 13-35 s, recipe in the caption plus "сохрани". The product is a tool in the frame, not a spec list. Winning topics for SM23: beshbarmak dough, manty, pizza from lepeshka, month of prep, baursaky.

## 2. Accounts
@ataria.kz = combines/kitchen tech only. Pillows go to the separate pillow account.

## 3. Production
1. Storyboard table: shot, seconds, on-screen text.
2. One frame at a time in Higgsfield (`nano_banana_pro`, 9:16, 2k) with product references from ataria-design-check. Run ataria-design-check; show Alisher only passing frames; wait for his "ок" before the next step.
3. Animate approved frames (image-to-video), 3-5 s each.
4. Montage in HyperFrames (installed in the scratchpad, telemetry off): `hyperframes init <name> --non-interactive --resolution portrait`, local gsap from node_modules (no CDN), `hyperframes check`, `hyperframes render -o out.mp4`. Verify a frame with ffmpeg before sending.
5. Caption: hook line, short recipe, Kaspi CTA, 8-12 hashtags.

## 4. Publish
Only after Alisher's explicit "да" (Windsor `create_video_post` for @ataria.kz).
