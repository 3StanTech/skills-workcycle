#!/bin/sh
# install.sh — link this bundle into the flat layout every host reads.
#
# Usage: install.sh [--check]
#   skills/<name>/ (with SKILL.md) -> $HOME/.agents/skills/<name>
#   hooks/<file> (not test_*)      -> $HOME/.agents/hooks/<file>
#   scripts/<file>                 -> $HOME/.agents/scripts/<file>
# Never replaces a real file or folder, or a link pointing elsewhere: reported as conflict.
# Idempotent. After installing, run ~/.agents/scripts/link-hosts.sh for Claude/Hermes/Pi.
#   --check  change nothing; print `bundlelink<TAB><bundle><TAB><missing|conflict|broken> <dest>`
#            per finding; exit 1 if any.
# Exit 0 ok, 1 findings/conflicts, 2 bad usage.
set -u

check=0
case "${1:-}" in
  "") ;;
  --check) check=1 ;;
  *) echo "usage: install.sh [--check]" >&2; exit 2 ;;
esac
[ $# -le 1 ] || { echo "usage: install.sh [--check]" >&2; exit 2; }

BUNDLE=$(CDPATH= cd -P -- "$(dirname "$0")" && pwd)
name=$(basename "$BUNDLE")
linked=0 ok=0 bad=0

report() { printf 'bundlelink\t%s\t%s %s\n' "$name" "$1" "$2"; bad=$((bad + 1)); }
fail() { echo "install.sh: $1 failed: $2" >&2; bad=$((bad + 1)); }

# Collapse . and .. textually; print the absolute path.
normalize() {
  NORM_PATH="$1" awk 'BEGIN {
    p = ENVIRON["NORM_PATH"]; n = split(p, a, "/"); m = 0
    for (i = 1; i <= n; i++) {
      if (a[i] == "" || a[i] == ".") continue
      if (a[i] == "..") { if (m > 0) m--; continue }
      s[++m] = a[i]
    }
    out = ""; for (i = 1; i <= m; i++) out = out "/" s[i]
    print out
  }'
}

# A broken link is ours only if its normalized absolute target stays under $BUNDLE.
owned() {
  case "$1" in /*) ;; *) return 1 ;; esac
  case "$(normalize "$1")" in "$BUNDLE"/*) return 0 ;; *) return 1 ;; esac
}

link_one() {
  src=$1 dest=$2
  if [ -L "$dest" ]; then
    cur=$(readlink "$dest")
    if [ "$cur" = "$src" ]; then ok=$((ok + 1)); return; fi
    if [ -e "$dest" ]; then report conflict "$dest"; return; fi
    if ! owned "$cur" || [ "$check" -eq 1 ]; then report broken "$dest"; return; fi
    rm -f "$dest" || { fail rm "$dest"; return; }
  elif [ -e "$dest" ]; then
    report conflict "$dest"; return
  elif [ "$check" -eq 1 ]; then
    report missing "$dest"; return
  fi
  if ln -s "$src" "$dest"; then linked=$((linked + 1)); else fail ln "$dest"; fi
}

if [ "$check" -eq 0 ]; then
  mkdir -p "$HOME/.agents/skills" "$HOME/.agents/hooks" "$HOME/.agents/scripts" \
    || fail mkdir "$HOME/.agents/{skills,hooks,scripts}"
fi

for d in "$BUNDLE"/skills/*/; do
  [ -f "$d/SKILL.md" ] || continue
  n=$(basename "$d")
  link_one "$BUNDLE/skills/$n" "$HOME/.agents/skills/$n"
done
for f in "$BUNDLE"/hooks/*; do
  [ -f "$f" ] || continue
  n=$(basename "$f")
  case "$n" in test_*) continue ;; esac
  link_one "$BUNDLE/hooks/$n" "$HOME/.agents/hooks/$n"
done
for f in "$BUNDLE"/scripts/*; do
  [ -f "$f" ] || continue
  n=$(basename "$f")
  link_one "$BUNDLE/scripts/$n" "$HOME/.agents/scripts/$n"
done

[ "$check" -eq 1 ] || echo "linked=$linked ok=$ok conflict=$bad"
[ "$bad" -eq 0 ]
