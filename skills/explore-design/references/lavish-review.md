# Lavish review

The single owner of how mocks and decision pages are reviewed in Lavish. explore-design opens Lavish itself at Compare (the [live viewer](live-viewer.md)), at G4, in the optional Background step's live-switch review ([backgrounds](backgrounds.md#live-switch-review)) and for decision pages; the owner does not need to type `/lavish`. Current CLI guidance always wins over this file for commands and flags: `npx -y lavish-axi@0.1.97 --help`.

## Open

- Run from the mock's own folder: `npx -y lavish-axi@0.1.97 <mocks>/mock-a.html`. Lavish serves that folder, so assets use relative paths (`assets/img/hero.webp`), never root-relative `/` paths.
- Mocks render in the **project's own design system** (fonts, tokens, logo). Never restyle them with Lavish's fallback Tailwind/DaisyUI.
- To compare two or more mocks, open `compare.html` (the viewer). For one mock (Background, G4), open the mock itself: the same Options sheet docks inside it, so notes, switches and the final pick share one page.
- Tell the owner in one line which file is open and what to look at, after the [pre-flight](#before-the-owner-sees-it).

## Picks and decisions

- Any choice that can be seen leads with the [live viewer](live-viewer.md): one page, every option switched in place, one queued pick. No screenshot cards or contact sheets on the pick page.
- For a non-visual choice, build it into the page with the `input` playbook (`npx -y lavish-axi@0.1.97 playbook input`): native radios or checkboxes, the recommended option pre-selected, and one "Queue answer" per question that sends exactly one prompt.
- The `comparison` playbook remains for non-mock exhibits on decision pages; sample mocks are compared in the viewer.

## Works inside Lavish

Lavish runs every page at an opaque origin (the sandbox table and the causes: [live viewer](live-viewer.md#works-inside-lavish)).

- Classic scripts only; data embedded, never fetched from a local file; fonts embedded or system, never a remote font link.
- Every linked page lives inside the served folder; `mock-live.js` carries the state across links.
- `postMessage` to `'*'`, checked by `e.source` and type; every storage call in try/catch.
- Test with `node tools/sandbox-e2e.mjs`: the browser pane cannot capture sandboxed frames.
- A mock made from a site build goes through `tools/sandbox-prep.mjs` in place; never build a second Lavish-only copy.

## Before the owner sees it

The pre-flight, in order, before any "ready" message:

1. For a viewer or a docked mock: `node tools/sandbox-prep.mjs --check` and `node tools/sandbox-e2e.mjs` exit 0. A page with no viewer or mock contract (a decision page on the `input` playbook) skips this step and goes straight to 2.
2. Open the page in Lavish and start the poll. Lavish opens the owner's browser itself, and that window runs its layout check a few seconds after the load.
3. Run `node tools/lavish-warnings.mjs <file>`: Lavish's own layout findings for that page (it checks five rules at a 1080px desktop window). Lavish records a pass only when the findings change and keeps no "page ready" record, so a clean page cannot be confirmed: the tool exits 3 ("no findings recorded, unconfirmed") once the load has started and the wait runs out.
4. Fix every open finding it prints (exit 1) and repeat 3, at most three passes; then tell the owner what remains.
5. Only then send the one-line "open and ready" message. Exit 3 is reported in it as "no layout findings recorded (Lavish cannot confirm a clean pass)"; exit 2 (the page never loaded, or Lavish recorded a load failure) as "layout not pre-checked". Neither is skipped silently.

After the ready message the inbox rule returns: fix only what the owner queues.

**Known fixes** for the findings that recur:

- A skip link is hidden in place (clipped to 1px at the top-left, restored on `:focus`), never parked off-screen.
- Folded content is `display: none` or `hidden` (with `transition-behavior: allow-discrete` when it must fade), never clipped by height or hidden with `visibility`.
- Decorative layers are trimmed by their own section (`overflow: clip`), never allowed to widen `main`.
- Any fixed review control sits inside 1080×700.
- Text never overlaps at 1080.

## Polling (per host)

| Host | How |
|---|---|
| Claude Code | `npx -y lavish-axi@0.1.97 poll <file>` through the Bash tool with `run_in_background`, a tracked job that wakes the session when feedback arrives. Re-run it if it stops; queued feedback is kept |
| Codex, Grok | Foreground `npx -y lavish-axi@0.1.97 poll <file>`; it waits silently until feedback, then returns it |

Never use `nohup`, `&`, `disown` or a detached terminal. If the poll returns `browser_disconnected`, ask the owner whether to reopen or end; do neither uninvited.

## Apply feedback

- Each annotation lands on a real element: apply it as a **targeted edit to that element**. Never regenerate the page.
- **Stuck pick:** when the owner says something feels off but cannot say what, do not guess one fix. Add two to four versions of that one element as an option in the docked sheet, let the owner pick, then confirm the pick in the full page before moving on.
- Re-screenshot only what changed, at phone and desktop width, and show it in chat.
- Hand the result back with `npx -y lavish-axi@0.1.97 poll <file> --agent-reply "<what changed>"` when more review follows, or `npx -y lavish-axi@0.1.97 reply <file> --agent-reply "<…>"` when it does not.
- Layout warnings stay in the owner's Layout issues inbox; fix only the ones the owner queues (the [pre-flight](#before-the-owner-sees-it) is the one exception, before the first ready message). Lavish checks layout at a 1080px-wide desktop window and flags controls outside the viewport, which is why the Options sheet must fit 1080×700.

## Session hygiene

- Every Options sheet ends in a queue button (the template enforces it; any hand-built switch panel must match).
- A rebuild that touches more than one file is written in full before any file is replaced (`sandbox-prep.mjs` writes every file to a temp name, then renames them back to back, pages last; otherwise build in a temp folder and rename).
- Lavish reloads the open window when the opened file changes, and when any file in its folder changes if the page's `<html>` carries `data-lavish-live-reload-root` (the template's pages do, so an edit to a shared script or another mock reloads too). An editor that saves by replacing the file can slip past a single-file watch. After an edit, check that the session's `artifact_revision` rose and a load of it started (`artifact_load` in `~/.lavish-axi/state.json`), and tell the owner to reload **only** when that check says it did not.
- In a docked mock, a page link opens the linked page without Lavish's annotation and queue tools (Lavish adds them only to the page it opened). Review each page as its own Lavish session; the viewer is the place to move between pages.
- When the owner's note can be read two ways (a word, or the icon beside it), apply the likelier reading and name the other in the reply.
- Record each opened file in the README gate log.

## Finish

1. Record the pick and the date in the mocks README gate log.
2. Export the approved mock as one portable file: `npx -y lavish-axi@0.1.97 export <mock> --out <mocks>/approved/<name>.html`, then `node tools/sandbox-e2e.mjs --portable <exported file>`; if it fails, `node tools/sandbox-prep.mjs --portable <exported file>` and re-run.
3. End **every** session this round opened (each file in the gate log), not only the last: `npx -y lavish-axi@0.1.97 end <file>`.

## Cloud sessions

Lavish never runs in a cloud session (`CLAUDE_CODE_REMOTE=true`, including a Claude Project's cloud threads): its server would run inside the cloud VM, which the owner's browser cannot reach, and the VM pauses while the poll waits. No tunnel, no `LAVISH_AXI_ALLOWED_HOSTS` workaround, no `share`. Every Lavish step (Compare, Background, G4, decision pages) goes one of two ways instead; ask which (decision point):

1. **On the owner's machine (Recommended when it is on).** Rewrite the mocks README's Start here at the current gate, then ask for the go to commit and push the repo that holds the mocks folder. The handoffs root must be a git repo the machine can pull; if it is not, say so and use route 2. Give the paste line `resume from <mocks README path>`. The owner starts it in a thread on their computer: in a Claude Project, **Work locally** in the **+** menu (or ask the project conversation to run that thread on their computer); outside a project, a local session. That thread pulls, runs the Lavish step as usual, rewrites Start here, pushes with the owner's go, and the cloud work resumes from the README.
2. **Artifact stand-in (the machine is off).** Publish the page as a private Claude Artifact and collect the owner's comments on it in place of Lavish annotations; picks the docked sheet would queue are asked as decision points in chat. Without the Artifact tool, show screenshots in chat. "Works inside Lavish" and the pre-flight still apply. Note in the README that this gate ran without Lavish.

## Never

- `lavish-axi share` (it publishes to a third-party host).
- Lavish files inside a git working tree (Lavish's own default is `.lavish/` in the current folder, so always pass a path in the mocks folder).
- Using Lavish as an editor for production source pages.
