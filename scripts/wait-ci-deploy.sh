#!/bin/bash
# Bounded wait for CI runs, deploy statuses and app check runs on the pushed commit (full SHA).
# usage: [NETLIFY_TOKEN_FILE=PATH] wait-ci-deploy.sh [--sha SHA] [--timeout SECONDS] [--repo OWNER/NAME]
# Exit: 0 success, 1 failure, 2 timeout, 3 none-found (no runs, statuses, checks or Netlify deploy), 4 usage/tool error.
# Actions runs: `gh run list --commit`; commit statuses (Vercel, Netlify notifications): combined
# status API; other GitHub Apps: check-runs API, excluding github-actions so Actions count once.
# Never treats "nothing found" as "still running" or as passing.
# Netlify: for a repo mapped in netlify-sites.json (~/.agents/scripts/netlify-sites.json, kept out of the
# repo) and only while GitHub shows nothing, the production deploy for the full SHA is read from the Netlify deploys API with the token
# in ${NETLIFY_TOKEN_FILE:-~/.agents/secrets/netlify-token}: ready success, error failure, else pending.
set -uo pipefail

sha= timeout=900 repo= step=15 grace=120
usage_error() { echo "ERROR: $1" >&2; sed -n 3p "$0" >&2; exit 4; }
while [ $# -gt 0 ]; do
  case "$1" in
    --sha|--timeout|--repo)
      [ $# -ge 2 ] || usage_error "$1 needs a value"
      case "$1" in --sha) sha=$2 ;; --timeout) timeout=$2 ;; --repo) repo=$2 ;; esac
      shift 2 ;;
    -h|--help) sed -n 2,10p "$0"; exit 0 ;;
    *) usage_error "unknown argument: $1" ;;
  esac
done
command -v gh >/dev/null || { echo "ERROR: gh not found" >&2; exit 4; }
sha=$(git rev-parse "${sha:-HEAD}") || { echo "ERROR: cannot resolve commit" >&2; exit 4; }
[ -n "$repo" ] || repo=$(gh repo view --json nameWithOwner -q .nameWithOwner) || { echo "ERROR: cannot resolve repo" >&2; exit 4; }
case "$timeout" in ''|*[!0-9]*) echo "ERROR: --timeout must be seconds" >&2; exit 4 ;; esac


map_file="$HOME/.agents/scripts/netlify-sites.json" site_id=
if [ -f "$map_file" ]; then
  command -v jq >/dev/null || { echo "ERROR: jq not found (needed for $map_file)" >&2; exit 4; }
  site_id=$(jq -r --arg r "$repo" '.[$r] // empty | strings' "$map_file" 2>/dev/null) || site_id=
fi

echo "commit $repo@${sha:0:7} (full $sha), timeout ${timeout}s${site_id:+, netlify site $site_id}"
start=$(date +%s)
elapsed() { echo $(( $(date +%s) - start )); }

runs_state() {  # prints "<n> <pending> <failed>" for Actions runs on the full SHA
  gh run list --repo "$repo" --commit "$sha" --json status,conclusion \
    -q '"\(length) \([.[] | select(.status != "completed")] | length) \([.[] | select(.status == "completed" and (.conclusion != "success" and .conclusion != "skipped" and .conclusion != "neutral"))] | length)"'
}
status_state() {  # prints "<n> <pending> <failed>" for commit statuses
  gh api "repos/$repo/commits/$sha/status" \
    -q '"\(.statuses | length) \([.statuses[] | select(.state == "pending")] | length) \([.statuses[] | select(.state == "failure" or .state == "error")] | length)"'
}
checks_jq='.check_runs[] | select(.app.slug != "github-actions")'
checks_state() {  # prints "<n> <pending> <failed>" for non-Actions app check runs, all pages
  local rows
  rows=$(gh api --paginate "repos/$repo/commits/$sha/check-runs?per_page=100" \
    -q "$checks_jq"' | "\(.status) \(.conclusion)"') || return 1
  count_checks <<<"$rows"
}
# Newest production deploy for the full SHA as "<state> <site name> <url>"; nothing when none matches.
netlify_jq='[.[] | select(.commit_ref == $sha and .context == "production")] | sort_by(.created_at) | last
  | select(. != null) | "\(.state) \(.name // $site) \(.deploy_ssl_url // .admin_url // "-")"'
netlify_token=${NETLIFY_TOKEN_FILE:-$HOME/.agents/secrets/netlify-token} netlify_ok=
netlify_get() {  # GET Netlify API path; prints the body; never prints the token. Returns 2 past the overall deadline.
  local out code left
  [ -r "$netlify_token" ] && [ -s "$netlify_token" ] \
    || { echo "ERROR: Netlify token missing or unreadable: $netlify_token" >&2; return 1; }
  left=$(( timeout - $(elapsed) ))
  [ "$left" -gt 0 ] || return 2
  out=$(printf 'Authorization: Bearer %s\n' "$(cat "$netlify_token")" \
    | curl -sS -H @- --connect-timeout $(( left < 10 ? left : 10 )) --max-time $(( left < 30 ? left : 30 )) \
        -w '\n%{http_code}' "https://api.netlify.com/api/v1/$1") \
    || { [ "$(elapsed)" -ge "$timeout" ] && return 2; echo "ERROR: Netlify request failed: $1" >&2; return 1; }
  code=${out##*$'\n'}
  case "$code" in
    2??) printf '%s\n' "${out%$'\n'*}" ;;
    401|403) echo "ERROR: Netlify rejected the token in $netlify_token (HTTP $code)" >&2; return 1 ;;
    *) echo "ERROR: Netlify API returned HTTP $code for $1" >&2; return 1 ;;
  esac
}
netlify_state() {  # prints the netlify_jq line for $site_id
  local body
  body=$(netlify_get "sites/$site_id/deploys?per_page=20") || return $?
  jq -r --arg sha "$sha" --arg site "$site_id" "$netlify_jq" <<<"$body" \
    || { echo "ERROR: cannot parse Netlify deploys response" >&2; return 1; }
}
count_checks() {  # stdin: one "<status> <conclusion>" line per check run
  awk 'NF { n++; if ($1 != "completed") p++; else if ($2 != "success" && $2 != "skipped" && $2 != "neutral") f++ }
       END { print n+0, p+0, f+0 }'
}

netlify_exit() {  # $1 = netlify_get status: 2 is the overall deadline, anything else a tool error
  [ "$1" -eq 2 ] || exit 4
  echo "RESULT timeout after $(elapsed)s (Netlify request reached the ${timeout}s deadline)"; exit 2
}

while :; do
  r=$(runs_state) || { echo "ERROR: gh run list failed" >&2; exit 4; }
  s=$(status_state) || { echo "ERROR: gh api status failed" >&2; exit 4; }
  c=$(checks_state) || { echo "ERROR: gh api check-runs failed" >&2; exit 4; }
  read -r rn rp rf <<<"$r"; read -r sn sp sf <<<"$s"; read -r cn cp cf <<<"$c"
  nst= nname= nurl= nmsg=
  if [ "$rn" -eq 0 ] && [ "$sn" -eq 0 ] && [ "$cn" -eq 0 ] && [ -n "$site_id" ]; then
    # Public sites list deploys even with a bad token, so check it once on /user.
    [ -n "$netlify_ok" ] || { netlify_get user >/dev/null || netlify_exit $?; netlify_ok=1; }
    n=$(netlify_state) || netlify_exit $?
    read -r nst nname nurl <<<"$n"
    nst=${nst:-none}; nmsg=", netlify $nst"
  fi
  t=$(elapsed)
  if [ "$nst" = ready ] || [ "$nst" = error ]; then
    break
  elif [ "$rn" -eq 0 ] && [ "$sn" -eq 0 ] && [ "$cn" -eq 0 ]; then
    if [ "$t" -ge "$grace" ] && [ "${nst:-none}" = none ]; then
      echo "RESULT none-found: no CI runs, deploy statuses or check runs${site_id:+, and no Netlify production deploy} after ${t}s"; exit 3
    fi
  elif [ "$rp" -eq 0 ] && [ "$sp" -eq 0 ] && [ "$cp" -eq 0 ]; then
    break
  fi
  if [ "$t" -ge "$timeout" ]; then echo "RESULT timeout after ${t}s (runs $rn pending $rp; statuses $sn pending $sp; checks $cn pending $cp$nmsg)"; exit 2; fi
  echo "  ${t}s: runs $rn (pending $rp), statuses $sn (pending $sp), checks $cn (pending $cp)$nmsg"
  sleep "$step"
done

gh run list --repo "$repo" --commit "$sha" --json name,conclusion,url -q '.[] | "  run \(.name): \(.conclusion) \(.url)"'
gh api "repos/$repo/commits/$sha/status" -q '.statuses[] | "  status \(.context): \(.state) \(.target_url // "")"'
gh api --paginate "repos/$repo/commits/$sha/check-runs?per_page=100" -q "$checks_jq"' | "  check \(.app.slug)/\(.name): \(.conclusion) \(.details_url // .html_url // "")"'
[ -z "$nst" ] || echo "  netlify $nname: $nst $nurl"
if [ "$rf" -gt 0 ] || [ "$sf" -gt 0 ] || [ "$cf" -gt 0 ] || [ "$nst" = error ]; then echo "RESULT failure after $(elapsed)s"; exit 1; fi
echo "RESULT success after $(elapsed)s (runs $rn, statuses $sn, checks $cn${nst:+, netlify 1})"
