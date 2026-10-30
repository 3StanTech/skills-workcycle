# Usability — full reference

The deep version of Pillar 2. Skim what's relevant; skip what isn't.

## Table of contents
- [Feedback & system status](#feedback--system-status)
- [Forms](#forms)
- [Navigation & wayfinding](#navigation--wayfinding)
- [Accessibility](#accessibility)
- [Content & microcopy](#content--microcopy)
- [Cognitive load](#cognitive-load)
- [Destructive & irreversible actions](#destructive--irreversible-actions)

## Feedback & system status

- **Interaction states are non-negotiable.** Hover, `:focus-visible`, active,
  disabled — styled distinctly on every interactive element. `:focus-visible`
  (not bare `:focus`) gives keyboard users an indicator without flashing it at
  mouse users.
- **The async lifecycle**: idle → pending → success | failure. Every async
  action shows all applicable states. Pending: disable the trigger, change its
  label ("Save" → "Saving…"), and/or show a spinner *in place* (not a
  full-screen takeover for a small action). Success: visible confirmation —
  toast, inline check, state change. Failure: message near the point of
  action.
- **Perceived speed**: under ~100ms feels instant — no indicator needed;
  100ms–1s — subtle indicator; over ~1s — explicit progress; over ~10s —
  progress + the option to leave and come back. Skeleton screens beat
  spinners for content loads (they set shape expectations and reduce
  perceived wait).
- **Optimistic UI** (update immediately, reconcile with server) is great for
  low-stakes, high-frequency actions (likes, toggles, reorders) — but it
  requires a rollback path and an error surface when the server disagrees.
  For high-stakes actions (payments, deletes, sends), wait for confirmation.
- **Never fail silently.** A caught error that only reaches `console.error`
  is invisible to the user; something in the UI must change.

## Forms

- **Field layout:** label above the field, optional helper text below the label or
  field, error text directly below the field. Keep the order the same for every field.
- **Every input has a `<label>`** (or `aria-label` when a visual label is
  truly impossible). Placeholder-as-label disappears on first keystroke and
  fails contrast; it is not a label.
- **Correct types and attributes**: `type="email" | tel | url | number |
  date`, `inputmode` where finer control is needed, `autocomplete` attributes
  (`name`, `email`, `street-address`…) so browsers can fill them.
- **Validation strategy**: validate on blur or on submit — not on every
  keystroke while the user is still typing (premature red is hostile). After
  first submit attempt, live-revalidate so errors clear as they're fixed.
- **Error messages** appear next to the field, in plain language, saying how
  to fix it ("Password needs at least 8 characters" not "Invalid input").
  On submit failure, move focus to the first error (and `aria-describedby`
  ties message to field).
- **Reduce the form**: every field costs completions. Defer optional data,
  derive what you can, mark the *optional* fields (if most are required)
  rather than starring everything.
- **Don't clear the form on failure.** Preserving user input across errors is
  the cheapest goodwill you'll ever buy.
- **Multi-step forms**: show progress, allow going back without data loss,
  and put the summary before the final commit.

## Navigation & wayfinding

- **Users should always know where they are**: current page/section indicated
  in nav, page titles that match the link that got them there, breadcrumbs on
  deep hierarchies.
- **Links look like links, buttons like buttons** — and semantically *are*
  (`<a href>` navigates, `<button>` acts). Divs with click handlers break
  keyboard, screen readers, middle-click, and right-click-copy-link all at
  once.
- **Back must work.** SPAs that break the back button or scroll position
  break the web's oldest contract. Sync meaningful state to the URL when
  views change.
- **No dead ends**: 404s, empty results, and error pages all offer a route
  onward (search, home, retry, suggestions).
- **Search behavior**: forgiving of case/whitespace, shows "no results"
  helpfully, preserves the query in the box.

## Accessibility

The floor, in rough priority order:

1. **Semantic HTML first.** `<button>`, `<a>`, `<nav>`, `<main>`, `<header>`,
   real `<h1>–<h6>` in hierarchical order, `<ul>` for lists, `<table>` for
   tabular data (with `<th scope>`). Semantics give you keyboard and screen
   reader behavior for free; ARIA is the patch you need when you deviate.
2. **Keyboard operability.** Every interaction reachable and operable by Tab /
   Enter / Space / arrows as appropriate. Logical tab order (usually: just
   don't fight DOM order). No keyboard traps. Escape closes overlays; focus
   moves *into* an opened modal and *returns to the trigger* on close.
3. **Visible focus.** A clear `:focus-visible` style — the default outline is
   acceptable; removing it without replacement is not.
4. **Contrast.** ~4.5:1 for body text, 3:1 for large text and essential UI
   glyphs (WCAG AA). Light-gray-on-white placeholder aesthetics routinely
   fail this.
5. **Images**: meaningful images get descriptive `alt`; decorative ones get
   `alt=""` (never omit the attribute).
6. **Color independence.** Status, validity, and selection each conveyed by
   at least one non-color signal (icon, text, weight, underline).
7. **Motion.** Wrap nontrivial animation in
   `@media (prefers-reduced-motion: no-preference)`, or reduce/disable under
   `prefers-reduced-motion: reduce`.
8. **ARIA when semantics run out**: `aria-expanded` on disclosure triggers,
   `aria-label` on icon-only buttons, `role="alert"` or `aria-live="polite"`
   for dynamic messages users must hear about, `aria-current="page"` in nav.
   First rule of ARIA: prefer the native element that makes it unnecessary.
9. **Forms** (see above): labels, described-by error wiring, focus-to-first-
   error.

## Content & microcopy

- **Buttons say what they do**: "Save changes", "Delete 3 items" — not "OK" /
  "Submit" / "Yes". In confirmations, the button label should make the dialog
  body optional reading.
- **Front-load information**: first words of headings, links, and list items
  carry the meaning (people scan the left edge).
- **Speak user, not system**: "Couldn't save — you're offline" beats
  "Error 5003: persistence layer unreachable". Log the code; show the human
  version (a small "details" affordance can expose the code for support).
- **Empty states teach**: what this area is for + how to put the first thing
  in it. A blank panel reads as broken.
- **Numbers, dates, and units formatted for reading**: thousands separators,
  relative dates where recency matters ("2 hours ago") with absolute on
  hover/secondary, explicit units.

## Cognitive load

- **One primary action per view.** Visual dominance goes to the thing most
  users came to do; everything else is visibly secondary or tucked away.
- **Progressive disclosure**: defaults visible, power options behind
  "Advanced". Don't make the 90% case pay a complexity tax for the 10%.
- **Recognition over recall**: show recent choices, keep context visible
  across steps, never make users remember a value from a previous screen.
- **Consistency is a feature**: same term, same icon, same placement for the
  same concept everywhere. Internal consistency beats novelty.
- **Sensible defaults, remembered preferences.** The best interaction is the
  one the user didn't have to perform.

## Destructive & irreversible actions

- Confirm proportionally to the blast radius: a toast-with-undo beats a
  confirm dialog for small reversible deletes; typed confirmation ("type the
  project name") is reserved for the truly catastrophic.
- **Undo > confirm** wherever feasible — confirmation dialogs get reflexively
  clicked through; undo actually saves people.
- Destructive buttons: visually distinct (danger color), physically separated
  from safe actions, never the default focused button in a dialog.
- Soft-delete with a grace window when the data model allows it.
