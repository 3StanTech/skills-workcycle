---
name: be-ambitious
description: >-
  Turn a task or prompt into a deeper version of itself, not a bigger one:
  name the field, say what a top professional would do that was not asked for,
  the rawest source material, the specific methods and tools, and what outside
  check would show the result is right; then rewrite the prompt to ask for
  exactly that. Trigger: /be-ambitious, $be-ambitious, "be ambitious", "make
  this prompt deeper", "what would an expert do here", "raise the bar on this
  task", "rewrite my prompt like a pro would ask it". Not for expanding scope,
  adding features, or polishing tone or length; not for discovery (explore).
---

# Be ambitious

Adapted from a prompt shared by Felix Rieseberg (Anthropic):

> I want a deeper version of this task, not a bigger one. Before rewriting it:
> (1) say what a top professional in this field would do here that I'm not
> asking for; (2) name the rawest material they would start from instead of
> what has already been digested for me; (3) name the specific methods and
> tools they would use; (4) say what, other than you or me, would show the
> result is right. Then rewrite my prompt to ask for exactly that.

**Decision points:** If an interactive question tool (e.g. `AskUserQuestion`) is available, use it with 2–4 prefilled options, recommended option first and labeled "(Recommended)". Otherwise, print the same options as a numbered list in chat, state the recommended number, and wait for a reply.

## Input

The task is whatever follows `/be-ambitious`. If nothing follows, use the user's most recent request in this conversation. If there is none, ask for the task in one line and stop.

## Deeper, not bigger

Keep the user's goal and scope. Depth means a higher standard for the same outcome: better sources, sharper methods, real verification. Do not add deliverables, features or side quests. If a suggestion would make the job larger rather than better, drop it.

## The four questions

This file is the only home of the four questions; other skills cite them by number.

Name the field first (e.g. "investigative journalism", "SRE incident response", "conversion copywriting"), then answer the four questions for that field. Be concrete: name the actual thing, not the category.

1. **What a top professional would do that wasn't asked for.** The two or three moves that separate expert work from competent work here, such as stating the decision the work serves, checking base rates, reproducing before fixing, or writing the counter-argument.
2. **The rawest material.** The primary sources they would start from instead of summaries: the dataset, not the chart; the filing, not the article; the logs and the code, not the bug report; the paper's methods section, not the abstract. Say where it lives if you know.
3. **Specific methods and tools.** Named techniques, instruments, libraries, commands or frameworks, and why each fits this task.
4. **What, other than the user or the model, would show it is right.** An external check: a test suite or benchmark, a reproduction, ground-truth data, a known answer to compare against, a measurement, a domain expert or reviewer, a real user's behaviour. Say what result counts as a pass and what counts as a failure.

If you don't know the field well enough to answer, say so rather than inventing a source or tool.

## Rewrite

Write the rewritten prompt in a single fenced block the user can copy. It asks for exactly what the four answers describe: start from the raw material, use the named methods, and end with the external check and its pass criterion. Keep it as long as it needs to be, in the user's voice.

**STOP** after the rewrite and ask one decision-point question:

- **Run it now:** do the rewritten task in this session.
- **Start `/explore` with it:** recommended when the task is a new feature, system or design; the rewrite becomes explore's input and question 4 becomes its Outside check.
- **Stop here:** the user copies the prompt.

Never start the task unasked.

## Used by

- `explore` and `explore-design` use questions 1–3 as the **expert lens** in their research stage.
- explore's restatement turns question 4 into the **Outside check** line under "Done looks like"; `create-plan` seeds a verification scenario from it.

## Guardrails

- Same goal, same scope; depth only.
- No invented sources, tools, datasets or experts.
- Stop after the rewrite; the user decides what runs.

## Origin

Adapted from DannyMac180's `be-ambitious` skill (MIT; see `NOTICE`).
