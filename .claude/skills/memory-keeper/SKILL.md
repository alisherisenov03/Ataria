---
name: memory-keeper
description: Keep Jarvis memory (Supabase jarvis.memory) clean and current. Separates long-term facts from fresh notes, merges duplicates, retires stale numbers, and fixes wrong facts. Use weekly, after a correction from Alisher ("это не так", "подушки в другом аккаунте"), or when Jarvis gives an outdated number.
---

# Memory keeper: old and new memory

Memory lives in `jarvis.memory` (project `pepexjsboutlqmqjyemc`), kinds: `fact`, `preference`, `lesson`, `skill`. `standing_context()` loads the 12 newest `fact`/`preference` rows into every Jarvis prompt, so stale rows cost accuracy.

## Old memory (long-term)
Preferences, rules, brand facts, account structure (e.g. @ataria.kz = combines only; pillows have a separate account). Keep until Alisher changes them.

## New memory (expires)
Numbers with a date: prices, followers, reach, trends, competitor prices. Each must contain its date. Older than 30 days: re-check or delete.

## Procedure
1. `select id, kind, created_at, content from jarvis.memory order by created_at desc`.
2. Duplicates or contradictions: keep the newest correct one, update the text, delete the rest.
3. A correction from Alisher always wins: `update` the wrong row at once, never add a second contradicting row.
4. Exact Kaspi money numbers do not belong in memory: they come live from the cabinet mirror (`jarvis.cabinet_snapshot`) and Kaspi tables.
5. Report in one line what changed.
