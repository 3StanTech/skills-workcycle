# Mobile screen concepts

App screen concepts and flows as images (or coded screens when the brand is set). No
SwiftUI, Flutter, React Native, or production app code in this mode. Scope, count and
approval belong to [medium and providers](medium-and-providers.md).

## 1. Decide first

- **Platform feel:** iOS-native (calm hierarchy, tab bar, sheets, restrained chrome),
  Android-native (firmer app bars, bottom nav, explicit states), or cross-platform
  neutral. Pick one and stay coherent.
- **Screens:** exactly the agreed screens and flow. Propose a scope change before adding
  onboarding or extra flows; add a detail render only to fix a concrete readability gap.
- **Presentation:** a clean phone frame by default (same device, scale and even margins
  across the set; content stays the hero). Raw screens when the brief asks.

## 2. Lock a design bible before screen 2

Platform feel, palette, type mood and scale, spacing, radius, icon style, imagery
treatment, texture strength, navigation model, card/list behavior, button style, shadows.
Every later screen belongs to the same product.

## 3. Screen rules

- **Real app, not a website in a phone:** respect status bar, safe areas, home indicator,
  bottom nav and sheet zones.
- **First screen:** one focal point, 1–3 short lines, one clear action; no stat chips,
  pills, or overlapping cards.
- **Flow logic:** screen order must be a believable journey (onboarding → auth → home,
  browse → detail → cart). Vary composition, density and image balance between
  screens without changing the system.
- **Onboarding:** distinct compositions per slide, short copy, no early rating prompts.
- **Navigation:** familiar patterns (tabs for top-level, stack for drill-down, sheets for
  secondary tasks); one obvious primary path.
- **Layout:** fewer, clearer containers; no box-in-box stacks, widget walls, or fake
  system labels.

## 4. Readability

Text must never feel small. If it does, cut content, enlarge, add space, or split the
screen. Protect text over imagery with fades, masks, or scrims. Short, believable copy:
real screen titles and button labels, no inspirational filler.

## 5. Art direction

- Use imagery when the category benefits (food, commerce, travel, social, wellness,
  editorial): onboarding heroes, product and media cards, image headers with fades.
  Fixed aspect ratios, one treatment across the set.
- Controlled texture (grain, paper, soft noise) where it supports the mood; never over
  text.
- A few clean accents (line marks, arcs, small glyphs); no sticker spam.
- Iconography with consistent weight and some character, not default library icons.
- One clean palette with one or two working accents; no purple-blue AI gradients or
  muddy saturation.
- "Not always simple, always clean": rich layered screens are fine if hierarchy holds.

## 6. Category bias

| Category | Lean toward |
|---|---|
| Fintech | Trust, calm spacing, clear numbers, restrained accents, no chart spam |
| Health / fitness | Strong metric hierarchy, airy spacing, optimistic imagery |
| Productivity | List/card discipline, simple navigation, calm density |
| Social | Profile/feed rhythm, expressive media, clear create vs browse |
| Commerce / food | Strong product imagery, stable card ratios, clean checkout |
| Wellness / lifestyle | Soft materials, calm type, tactile backgrounds |

## 7. Check before showing

Real app feel and safe areas · first screen clean · readable type everywhere · flow
logical and complete · consistent system and device framing · no mobile AI tells (glass
cards, blobs, widget walls, filler copy) · regenerate weak screens instead of accepting
them.
