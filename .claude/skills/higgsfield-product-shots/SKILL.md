---
name: higgsfield-product-shots
description: Generate accurate Ataria product photos and reel frames in Higgsfield from the real reference photos. Use for "сделай фото", "карточка", "кадр", "макет", product visuals.
---

# Higgsfield product shots

Workspace e4ce0c3d-dd45-4770-9aea-408439154e87 (plan plus). Projects: pillows 1c8faed0-664f-460d-88b4-8d642e33e096, "Food Processor Gift" a0959ada-d1ac-4b19-af07-73f5eedf64e1. Media library holds ~200 uploads: product photos, catalog renders, plus WhatsApp screenshots and personal photos (never use those).

Model: `nano_banana_pro`, 2k, aspect per use (9:16 reels, 4:5 feed, 1:1 Kaspi). Pass 2–3 references with role `image_references`.
Prompt pattern: start with "EXACT COPY of the product in the reference photos", then list the distinctive parts (see ataria-design-check), then "do not redesign any part", then scene, light, "no people faces, no text, no watermark".
Wait: `jobs_wait` with jobs [{job_id, index}], timeout 15.
Always run ataria-design-check side by side with the reference before showing. First attempts often redesign the product: regenerate with a stricter description instead of showing it.
