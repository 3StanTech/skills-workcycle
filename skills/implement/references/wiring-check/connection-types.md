# Connection types — the full trace checklist

The exhaustive per-category sweep for Step 1–2. Use the categories that exist
in the project; skip the rest. For each item the question is always the same
pair: **does the reference resolve?** and **does it resolve to the intended
thing?**

## Table of contents
- [UI → behavior wiring](#ui--behavior-wiring)
- [Navigation & routing](#navigation--routing)
- [Forms & inputs](#forms--inputs)
- [Imports, exports & modules](#imports-exports--modules)
- [Assets & static references](#assets--static-references)
- [Data flow & state](#data-flow--state)
- [API & backend connections](#api--backend-connections)
- [CSS ↔ markup](#css--markup)
- [Config, env & build wiring](#config-env--build-wiring)
- [Cross-page / cross-component consistency](#cross-page--cross-component-consistency)
- [Common orphan patterns](#common-orphan-patterns)

## UI → behavior wiring

- Every `onclick`/`onClick`/`addEventListener` names a function that exists,
  in scope, spelled identically (the classic: handler renamed, one call site
  missed).
- Every visible interactive control *has* a handler or href — a button that
  does nothing is a broken promise to the user.
- Handlers receive what they expect (event object, the right arguments,
  the right `this`/binding where relevant).
- Toggles/switches actually toggle observable state; the state change reaches
  the UI (not just a variable nobody renders).
- Keyboard paths wired where custom controls exist (Enter/Space on
  role=button, Escape on modals).
- Event delegation targets still match after markup changes (selector-based
  listeners are silent breakers).

## Navigation & routing

- Every `<a href>` / router link points at a route or page that exists —
  including anchor targets (`#section` has an element with that id).
- Every registered route renders an existing component/view; no route paths
  registered to deleted components.
- Reverse check: every page/view that should be reachable *is* linked from
  somewhere (or confirmed direct-URL-only in the notes file).
- Dynamic route params consumed correctly (`/item/:id` → the view actually
  reads `id`).
- Redirects land somewhere real; fallback/404 route exists and renders.
- Back-button behavior sane in SPAs (navigation updates history where users
  would expect).
- External links open where intended (and `rel="noopener"` on
  `target="_blank"`).

## Forms & inputs

- Every form has a submit path: an `onSubmit`/action that exists and fires
  (test: does anything observable happen on submit?).
- Every field is captured: name/id/state binding present, value actually read
  by the submit handler (fields collected-but-ignored → uncertain-intent
  question).
- Field names match what the endpoint/handler expects on the other side
  (`email` vs `emailAddress` mismatches vanish silently).
- Validation wired: rules fire, messages render near fields, invalid submit
  is actually blocked.
- Default/prefilled values load from where they claim to.
- Reset/cancel controls do what their label says.
- Success and failure of submission both produce visible results (silent
  submission is a wiring bug even when the data arrives).

## Imports, exports & modules

- Every import resolves: path correct (relative depth, extension where
  required), file exists, case matches exactly (case-insensitive dev
  machines hide case bugs that break on Linux deploys).
- Named imports match actual exports (renamed export, stale import).
- Default vs named import agrees with the export style.
- No circular imports producing undefined-at-runtime.
- Script tags in HTML: correct paths, correct order (dependency before
  dependent), `defer` consistency.
- Reverse check: exports nothing imports → orphan list.

## Assets & static references

- Every `src`/`href`/`url()` resolves to a file that exists at that path in
  the *served* layout (build output paths differ from source paths — check
  against what deploys).
- Case sensitivity again — `Logo.PNG` vs `logo.png`.
- Fonts declared in `@font-face` exist and are actually applied somewhere;
  families used in CSS are actually loaded.
- Favicon/manifest/meta image paths resolve.
- Icons render (icon set imported, names valid in the set's current version).
- No hotlinks to dev-only URLs (`localhost:3000/img/...`) that die in
  production.
- Reverse check: sizeable assets in the project no code references → orphans.

## Data flow & state

- Every piece of state is both written *and* read: set-but-never-rendered
  and rendered-but-never-set are both findings.
- Props passed match props consumed: child expects `items`, parent sends
  `data` → silent undefined.
- Data transformations preserve the shape consumers expect downstream
  (rename/reshape in one layer, stale access in the next).
- Context/providers wrap the consumers that need them; consumers outside a
  provider fail quietly or with defaults.
- Derived values recompute from current sources (no stale copies captured at
  init).
- Persistence round-trips: what's saved (storage/API) is what load restores,
  key names identical.
- Loading/error state variables that exist are actually rendered somewhere.

## API & backend connections

- Every fetch/axios call targets a URL that exists — method, path, and any
  params match what the backend defines (or, for external APIs, what the
  docs say).
- Request payload shape matches what the endpoint reads; response shape
  matches what the frontend accesses (`data.items` vs `data.results`).
- Auth wired: tokens/headers attached where required; the failure path for
  expired auth does something visible.
- Both promise branches handled: success reaches the UI, error reaches the
  user (a `.catch(console.error)` is not "handled" from the user's chair).
- Reverse check on owned backends: endpoints nothing calls → orphans.
- Environment-dependent base URLs actually switch (dev URL hardcoded is a
  production breaker).
- Race protection where flows demand it (rapid re-request, stale response
  overwriting fresh).

## CSS ↔ markup

- Class names used in markup exist in stylesheets (typo'd class = silently
  unstyled); ID selectors match real IDs.
- Reverse: selectors matching nothing in the DOM → dead CSS (usually
  low-severity, but worth a line).
- CSS/JS shared hooks stay in sync (JS toggles class `open`, CSS styles
  `.opened` → broken feature).
- Media-query breakpoints consistent with the layout's actual breakpoints.
- Specificity/order accidents: styles defined but visibly not applied where
  intended.
- CSS custom properties referenced (`var(--brand)`) are defined on a
  reachable scope.

## Config, env & build wiring

- Every env var the code reads is declared (in `.env.example`, deployment
  config, or docs) — and vice versa, declared vars are read by something.
- Config keys accessed match config keys defined (nesting and spelling).
- Build entry points, output paths, and aliases in config match reality
  (`@/components` alias resolves; the build's `dist/` is what the host
  serves).
- Package.json scripts run (no references to deleted files or missing bins);
  dependencies used in code are actually in `dependencies` (not luck via a
  transitive install, not stranded in `devDependencies` if needed at
  runtime).
- Deployment config (e.g. `vercel.json` routes/crons/redirects) points at
  paths that exist in the project.

## Cross-page / cross-component consistency

- Shared components render consistently in every place they're used (a prop
  contract change fixed in three call sites out of four).
- Site-wide elements (header, footer, nav) present on every page that should
  have them, and identical where they should be identical.
- The same concept carries the same label/route everywhere ("Sign in" here,
  "Log in" there → at minimum a question).
- Feature parity where promised: if the mobile nav and desktop nav should
  expose the same destinations, verify they actually do.

## Common orphan patterns

High-yield places to look for defined-but-disconnected pieces:

- Functions/components exported but never imported anywhere.
- Event handlers defined but attached to nothing.
- Routes registered but never linked (confirm intent — may be deliberate).
- State declared, initialized, and never read.
- CSS files or blocks no page includes.
- Form fields collected but absent from the submit payload.
- API endpoints (owned backend) with zero callers.
- Feature flags that no longer gate anything.
- TODO/FIXME markers adjacent to half-wired code — the strongest signal of
  "meant to connect this and forgot," and prime material for an
  uncertain-intent question rather than silent deletion.
