---
name: skill-reviewer
description: Review and improve the project's skills, including peer review where one skill checks another. Use when a skill is created or edited, when a skill gave a bad result, or for a periodic review of all skills in .claude/skills.
---

# Skill reviewer

Use `anthropic-skills:skill-creator` for authoring mechanics and evals; this skill is the review gate.

## Rubric (score each 0-2)
1. Trigger: the description says exactly when to use it, with Alisher-style phrases.
2. Concrete: real IDs, tables, commands, file paths, not generic advice.
3. Correct: facts match the current system (check code, tables, connectors).
4. Safe: no secrets, irreversible actions only with Alisher's "да".
5. Reuse: points to existing skills/connectors instead of duplicating them.
6. Short: nothing the model already knows by default.

## Peer review
For each skill A, review it from the angle of skill B that consumes it (e.g. ataria-reels is reviewed with ataria-design-check's rules; memory-keeper with self-improve's lessons). Contradictions between skills are bugs: fix the wrong one.

## Output
Append to `docs/skills-review-log.md`: date, skill, score, what changed. Then edit the skill. Score below 9 of 12: rewrite the weak parts now.
