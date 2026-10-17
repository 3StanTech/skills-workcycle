---
name: remind
description: >-
  Park a reminder in an existing project file (never a new one) so it resurfaces
  at the next /end or /handoff, the next session, the end of a roadmap
  phase, or on a date; also list or clear reminders. Trigger: /remind, "remind me
  (again) of X at/when/after …", "what reminders do I have", "clear the reminder
  about X". Not for durable facts (master.md via /end) or timed alerts (schedule).
---

# Remind

Store a one-line reminder where the next matching checkpoint will read it, and surface it there.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply. Never proceed past a decision point on an assumption.

## 1. Parse the reminder

From the user's words, take the **text** (what to remind) and the **when**. Map the when to one of:

| User says | `when:` value | Surfaced by |
|---|---|---|
| "at the end of this session", "before I close", "at the next /end" | `next close` | `/end`, `handoff` |
| "next session", "tomorrow when I start" | `next session` | `prime`, the SessionStart hook |
| "after Phase 2", "when this phase ships" | `end of Phase <N>` | `roadmap` Update when that phase ships or closes |
| "on Oct 6", "in a week" | `on <YYYY-MM-DD>` (absolute date) | the first checkpoint on or after that date |

No when given: use `next close`. Ambiguous: ask one decision-point question with these options.

## 2. Pick the file (existing files only)

1. `end of Phase <N>`, or an active roadmap governs the work: that `ROADMAP.md`, section `## Deferred owner reminders`.
2. Otherwise, the project's `master.md`, section `## Reminders`. Create the section if missing (it is a section, not a file).
3. No project, or no `master.md`: **keep it in this session only.** Say so in one line: it is lost if the session ends without being surfaced. Offer to attach it to a named project instead.

Never create a file for a reminder.

## 3. Write one line

```
- <text> (when: <when>; added <YYYY-MM-DD>)
```

Keep it to one line, in the owner's wording. No secrets. If the same reminder already exists, update its `when:` instead of adding a second line.

Confirm in chat with one line: `Reminder set for <when>, in <file>.`

## 4. List or clear

- **"What reminders do I have?"**: read only the `## Reminders` section of the current project's `master.md` and the active roadmap's `## Deferred owner reminders`. Print them grouped by `when:`, with due ones first.
- **"Clear the reminder about X"**: delete that line. If more than one matches, ask.

## 5. How checkpoints surface reminders

Checkpoint skills (`end`, `handoff`, `prime`, `roadmap`) follow this rule:

1. Read the reminder section of the file they already open. Never open extra files to look for reminders.
2. A reminder is **due** when its `when:` matches the checkpoint, or its date is today or earlier.
3. Show due reminders to the owner in the checkpoint's report, under a `Reminders` heading.
4. Then delete them from the file. `/end` also records them in the day's `CHANGELOG.md` entry, as `Reminded: <text>`. A `next session` reminder is deleted by the first `/end` after it has been shown. `prime` and `handoff` only show or carry a reminder; they never delete it.

## Output

One line in `master.md` `## Reminders` or `ROADMAP.md` `## Deferred owner reminders`, or nothing (session-only); a one-line confirmation in chat.

## Guardrails

- **Never create a new file** for a reminder.
- **Never store secrets** or confidential figures in a reminder.
- **Never act on a reminder.** Surface it; the owner decides.
- **Never drop a reminder silently.** Delete it only after it has been shown or the owner cleared it.
- **Not for durable facts:** a decision belongs in `master.md` (via `/end`) or the roadmap's Locked decisions.
