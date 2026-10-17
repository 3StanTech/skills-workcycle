# Lavish review

The single owner of how mocks and decision pages are reviewed in Lavish. explore-design opens Lavish itself at G4 and for decision pages; the owner does not need to type `/lavish`. Current CLI guidance always wins over this file for commands and flags: `npx -y lavish-axi --help`.

## Open

- Run from the mock's own folder: `npx -y lavish-axi <mocks>/mock-a.html`. Lavish serves that folder, so assets use relative paths (`assets/img/hero.webp`), never root-relative `/` paths.
- Mocks render in the **project's own design system** (fonts, tokens, logo). Never restyle them with Lavish's fallback Tailwind/DaisyUI.
- Tell the owner in one line which file is open and what to look at.

## Picks and decisions

- For a choice (direction, type pairing, mix), build it into the page with the `input` playbook (`npx -y lavish-axi playbook input`): native radios or checkboxes, the recommended option pre-selected, and one "Queue answer" per question that sends exactly one prompt.
- For a side-by-side, use the `comparison` playbook.

## Polling (per host)

| Host | How |
|---|---|
| Claude Code | `npx -y lavish-axi poll <file>` through the Bash tool with `run_in_background`, a tracked job that wakes the session when feedback arrives. Re-run it if it stops; queued feedback is kept |
| Codex, Grok | Foreground `npx -y lavish-axi poll <file>`; it waits silently until feedback, then returns it |

Never use `nohup`, `&`, `disown` or a detached terminal. If the poll returns `browser_disconnected`, ask the owner whether to reopen or end; do neither uninvited.

## Apply feedback

- Each annotation lands on a real element: apply it as a **targeted edit to that element**. Never regenerate the page.
- Re-screenshot only what changed, at phone and desktop width, and show it in chat.
- Hand the result back with `npx -y lavish-axi poll <file> --agent-reply "<what changed>"` when more review follows, or `npx -y lavish-axi reply <file> --agent-reply "<…>"` when it does not.
- Layout warnings stay in the owner's Layout issues inbox; fix only the ones the owner queues.

## Finish

1. Record the pick and the date in the mocks README gate log.
2. Export the approved mock as one portable file: `npx -y lavish-axi export <mock> --out <mocks>/approved/<name>.html`.
3. End the session: `npx -y lavish-axi end <file>`.

## Never

- `lavish-axi share` (it publishes to a third-party host).
- Lavish files inside a git working tree (Lavish's own default is `.lavish/` in the current folder, so always pass a path in the mocks folder).
- Using Lavish as an editor for production source pages.
