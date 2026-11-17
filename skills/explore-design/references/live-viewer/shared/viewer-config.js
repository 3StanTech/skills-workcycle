// Live viewer config (explore-design live-viewer template). Adapting the template means
// editing this file: the viewer (compare.html), the docked sheet inside each mock and the
// sandbox test all read it. A classic script on purpose: Lavish's sandbox refuses modules.
//
// mocks   the directions to compare; keys 1-9 pick them in the viewer. `rec` stars one and
//         pre-selects it; `why` is one line shown while it is selected.
// pages   each page of a mock; `file(mock)` returns its file name in this folder.
// options the choices that make up the pick. Each applies live inside the mock (no reload).
//         `only` limits an option to some mocks (disabled, not hidden, elsewhere); `start`
//         overrides the starting value (default: the `rec` choice, else the first).
// states  preview states, never part of the pick: `on`/`off` values; `reload: true` for a
//         flag the page reads once at load (the viewer reloads the frame for it).
// dockCorner  where the docked sheet's pill sits inside a single mock (default bottom-left).
window.VIEWER_CONFIG = {
  id: 'demo-pick',
  title: 'Pick the look, live',
  eyebrow: 'Live review',
  designWidth: 1440,
  phoneWidth: 390,
  dockCorner: 'bottom-left',
  mocks: [
    { value: 'a', label: 'A Calm', rec: true, why: 'Quiet type and wide margins: the menu does the selling.' },
    { value: 'b', label: 'B Bold', why: 'Big headline and a dense grid: more on the first screen.' },
  ],
  pages: [
    { value: 'home', label: 'Home', file: (mock) => `mock-${mock}.html` },
    { value: 'about', label: 'About', file: (mock) => `mock-${mock}-about.html` },
  ],
  options: [
    { key: 'accent', label: 'Accent', choices: [
      { value: 'warm', label: 'Warm', rec: true, why: 'Matches the bread photos.' },
      { value: 'cool', label: 'Cool', why: 'Reads calmer, colder on food.' },
    ] },
    { key: 'density', label: 'Density', only: ['b'], choices: [
      { value: 'airy', label: 'Airy', rec: true },
      { value: 'tight', label: 'Tight' },
    ] },
  ],
  states: [
    { key: 'menu', label: 'Menu', on: 'open', off: 'closed' },
    { key: 'motion', label: 'Still frame', on: 'off', off: 'on', reload: true },
  ],
};
