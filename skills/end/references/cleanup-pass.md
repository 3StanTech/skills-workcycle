# Cleanup pass

Offered once per workcycle, at roadmap Close or at `/end`, whichever comes first: list what the workcycle created that may no longer be needed, and delete only what the owner confirms. A *workcycle* is one roadmap initiative; without a roadmap, it is the work since the project's last `Cleanup:` marker.

## When to offer, and when not

- **Offer** when the workcycle created process artifacts outside the repo (scratch pages, test folders, exports, side sessions, temp profiles, running servers) and no marker for it exists yet.
- **Skip silently** when a marker already exists for this workcycle: a `Cleanup: done <date>` or `Cleanup: declined <date>` line in the governing roadmap's header, or, without a roadmap, in the project's newest `CHANGELOG.md` entry. A pass run at roadmap Close is never offered again by the next `/end`, and the reverse.
- **Skip** when the session created nothing to clean.

## What to list

Only items this workcycle created, with evidence (the session's own tool calls, the roadmap's runs folder, file dates inside the workcycle):

- Scratch and test files: throwaway pages, probe scripts, superseded evidence copies, test mocks for a fictional brief.
- Exports and downloads the session made (transcript zips, unpacked exports).
- Side sessions and helper sessions the workcycle started and no longer needs (archive, never delete, unless the owner asks).
- Leftovers on the machine: temp browser profiles, preview servers still listening, background jobs.
- Large evidence that nothing references any more, marked "evidence, keep by default".

Never list: the roadmap folder itself, plans, explore docs, findings files, approved mocks, anything committed, anything the owner made, and anything another project or session may still use. Uncertain ownership is a question, never a candidate.

## How

1. Build one table: path or item · what it is · size · why it may be unneeded · keep if. Group it (scratch, exports, sessions, machine leftovers, evidence).
2. Ask one decision-point question per group (delete / keep / let me choose), recommended option first; evidence groups default to keep.
3. Delete only what the owner confirmed. Prefer the least destructive route (move to Trash, archive a session, stop a server); permanent deletion only when the owner says so. Fix any doc line that pointed at a deleted path.
4. Record the marker the same turn: `Cleanup: done <YYYY-MM-DD> (<n> items removed; kept: <short list>)` or `Cleanup: declined <YYYY-MM-DD>`, in the roadmap header under `Status:`, or in the `/end` CHANGELOG entry when no roadmap governs the work.
