# Live viewer

How the owner picks between things they can see: one page where the real mock fills the window and an Options sheet switches every option in place, so the pick is the switch state. Used for Compare, the Background step, the G4 motion shortlist and visual decision pages. It ships as a copyable template, [`live-viewer/`](live-viewer/), with its own sandbox end-to-end test. Opening and polling are in [Lavish review](lavish-review.md); this file holds the pattern, the contract and the sandbox rules.

## Table of contents
- [When](#when)
- [The viewer](#the-viewer)
- [The mock contract](#the-mock-contract)
- [Works inside Lavish](#works-inside-lavish)
- [Start from the template](#start-from-the-template)
- [One mock: the docked sheet](#one-mock-the-docked-sheet)
- [Verify before handing back](#verify-before-handing-back)
- [Hand-off](#hand-off)

## When

- Lead with the viewer for any choice the owner can see: sample mocks at Compare, variants of one element, background effects, the motion shortlist, a visual decision on a [decision page](decision-page.md).
- Count decides the host: **two or more mocks** → `compare.html`, the viewer; **one mock** (Background, G4) → open that mock, and the same sheet docks inside it ([below](#one-mock-the-docked-sheet)). Lavish annotates elements of the page it serves, not of a mock nested in the viewer's frame, so element notes need the mock opened on its own.
- Non-visual choices stay on Lavish's `input` playbook.
- Screenshots and contact sheets are chat previews and README material, never the pick page.

## The viewer

- The real mock fills the window at its design width and scales down to fit; it is never a thumbnail.
- The Options sheet is non-modal: it opens and closes (✕, Esc, the floating pill) and fits a **1080×700** window, the size Lavish checks layout at.
- Every option applies live inside the mock. Only a change of mock or page, or a flag the page reads once (`reload: true`), reloads the frame.
- The recommended choice is starred and pre-selected; an option that does not apply to the current mock is disabled, not hidden.
- Preview states (menu open, still frame, Desktop/Phone width) sit apart from the pick, labelled "not the pick".
- Keys 1–9 switch mocks (never while typing). A mock or a choice may carry a one-line `why`, shown while it is selected: the owner compares reasons, not only looks.
- One form, one queued prompt with the full state and an optional note, a "Copy answers" fallback, an "Open full size" link. Every sheet ends in its queue button.
- No screenshots on the page.

## The mock contract

- **Initial state** from URL params (`?accent=warm&menu=closed&dock=0`); **live state** from `postMessage({ type: 'mock-set', values })` sent by the viewer.
- `shared/mock-live.js` mirrors every applied key on `<html data-KEY="value">` before calling the mock's handler, so CSS can style from it and the test can read it.
- Accept a message only when `e.source === window.parent` and its type is `mock-set`; never check the origin (it is opaque).
- `dock=0` (always sent by the viewer) marks `<html data-dock="0">`: in-mock review controls carry `data-review-dock` and hide under it.
- Same-folder page links carry the current state; links that leave the folder open a new tab.
- Under reduced motion a motion option is inert.

## Works inside Lavish

Lavish frames every page without `allow-same-origin`, so the page and every frame nested in it run at an opaque origin, even though `location.origin` still reads as the server's. Lavish serves the opened file's folder and what is under it, nothing above it, and never a root-relative (`/…`) path.

| Symptom | Cause | Rule |
|---|---|---|
| Scripts silently do nothing | Module scripts are fetched in CORS mode and refused | Classic scripts; a mock that keeps ES modules goes through `tools/sandbox-prep.mjs` |
| Data or a list renders empty | `fetch()` of a local file fails | Embed the data (prep's `bundle.data`, or an inline `window.__MOCK_DATA`) |
| Web fonts missing, fallback type | Font files are fetched in CORS mode and fail | Embed local fonts as data URIs with `sandbox-prep.mjs`; never a remote font link |
| Toggles do nothing, reloads work | `postMessage` to `location.origin` is dropped | Post to `'*'`; the mock checks `e.source` and the message type |
| A linked page opens without its menu, options or state | The page was outside the served folder, or the link dropped the state | Every linked page lives in the mocks folder; `mock-live.js` carries the state; outside links open a new tab |
| The page throws on load | Storage access throws | Every `localStorage`/`sessionStorage` call in try/catch |
| A canvas effect throws on local images | `getImageData` on a tainted canvas | Catch it and fall back |
| A browser-pane screenshot comes out black | The pane cannot capture a sandboxed frame | Use the test's `--shot` |

The flags were read from `lavish-axi@0.1.97` (`dist/cli.mjs`, the iframe with `id="artifact"`). After a pin bump, re-read them there and update `tools/sandbox-test.html` to match.

## Start from the template

| File | What it is |
|---|---|
| `compare.html` | The viewer: stage, frame, width fit |
| `shared/viewer-config.js` | `window.VIEWER_CONFIG`: mocks, pages, options, states. **Adapting means editing this file** |
| `shared/options-sheet.js` | The Options sheet, one script for both hosts (viewer and dock) |
| `shared/mock-live.js` | The mock side of the contract (`window.MockLive`) |
| `tools/sandbox-prep.mjs` | Makes the folder sandbox-safe in place; `--check` changes nothing; `--portable` finishes an export |
| `tools/sandbox-e2e.mjs` | The end-to-end test, framed with Lavish's flags |
| `tools/sandbox-test.html` | The harness that frames a page with those flags |
| `tools/lavish-warnings.mjs` | Prints Lavish's own open layout findings for the pre-flight |
| `mock-a.html`, `mock-b.html` (+ `-about` pages), `shared/demo.css`, `shared/src/`, `shared/mock.bundle.js`, `tools/prep.config.json` | Demo content; replace it |

1. Copy: `cp -R <skill>/references/live-viewer/. <mocks>/`. Never edit the template in place for a project.
2. Edit `shared/viewer-config.js`; replace the demo mocks. Each mock sets `<html data-mock="<value>">`, loads `shared/viewer-config.js`, `shared/options-sheet.js` and `shared/mock-live.js` as classic scripts (in that order), and calls `MockLive.init({ apply: { key: (value) => … } })`. Keys styled from `html[data-*]` need no handler.
3. **A hand-written mock:** classic scripts from the start, data inline, system or embedded fonts. Prep is needed only for ES modules (list them in `tools/prep.config.json` → `bundle`), local JSON or font files.
4. **A mock made from a site build:** copy the build output into the mocks folder, add `shared/` and `tools/`, run `node tools/sandbox-prep.mjs`, fix what it reports, run it again. Never keep a second Lavish-only copy.
5. Run `node tools/sandbox-prep.mjs` after editing any shared script (it re-stamps the `?v=` cache-bust on every page).

## One mock: the docked sheet

- Opened on its own (no `dock` param, as Lavish serves it), a mock mounts the same sheet inside itself: the options that apply to this mock, the preview states, a note, a verdict (Approve / Changes needed) and **Queue final pick**.
- It hides the mock, page and width rows; an option for other mocks only is disabled.
- The pill sits bottom-left (`dockCorner` moves it) and the sheet starts **closed**, so it never covers what the owner annotates.
- "Open in viewer" opens `compare.html` with the current state, for the phone width.
- The owner annotates elements of the page, flips options and queues the final pick from one page.

## Verify before handing back

- `node tools/sandbox-prep.mjs --check` and `node tools/sandbox-e2e.mjs` both exit 0 before a viewer or a docked mock is opened in Lavish.
- The test serves the folder on a free port, frames `compare.html` with Lavish's flags, and checks: both frames at an opaque origin; the sheet inside 1080×700; every option and choice applied in place (no reload); disabled options; preview states; mock and page switches carrying the values; Phone and Desktop widths; Esc and the pill; the copy fallback; fonts loaded; links followed inside the frame; number keys; why-notes; the docked sheet on the first mock; no sideways scroll; and no failed request or script error in the folder. `--url <Lavish session URL>` runs it against Lavish itself; `--shot <png>` saves the sandboxed page.
- Run both again after any edit to the template in the skill.
- After the open, the [pre-flight](lavish-review.md#before-the-owner-sees-it) reads Lavish's own layout findings before the owner is told the page is ready.

## Hand-off

- The pick (the full state plus the note and, in the dock, the verdict) goes into the mocks README gate log with the date.
- `compare.html`, the three shared review scripts and `tools/` are review chrome and never ship. `/implement` ports the picked values into the build.
