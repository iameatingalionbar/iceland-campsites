#!/usr/bin/env bash
# Build, verify and publish to GitHub Pages at the custom domain https://icelandcampsites.com
# (repo iameatingalionbar/iceland-campsites, gh-pages branch; the old github.io URL redirects there).
# Needs env var GITHUB_TOKEN_CAMPSITES (fine-grained, repo iameatingalionbar/iceland-campsites:
# Contents RW, Pages RW, Administration RW). The token is read from env only: never echoed, logged or stored.
# git auth comes from the repo-local credential.helper, which reads the same env var at runtime.
set -euo pipefail
cd "$(dirname "$0")"
OWNER=iameatingalionbar; REPO=iceland-campsites
DOMAIN=icelandcampsites.com   # also in data/site.json; build.py writes dist/CNAME from BASE_URL
export BASE_URL="https://${DOMAIN}"
API="https://api.github.com/repos/${OWNER}/${REPO}"
: "${GITHUB_TOKEN_CAMPSITES:?GITHUB_TOKEN_CAMPSITES is not set}"

echo "== build & checks"
python3 build.py
python3 check.py
python3 serve_check.py
python3 make_preview.py >/dev/null
touch dist/.nojekyll
[ "$(cat dist/CNAME)" = "$DOMAIN" ] || { echo "dist/CNAME missing or wrong"; exit 1; }

echo "== commit & push source (main)"
git add -A
if ! git diff --cached --quiet; then git commit -q -m "${DEPLOY_MSG:-Site update $(date +%F)}"; fi
git push origin main

echo "== force-push dist/ to gh-pages"
TMPIDX="$(mktemp)"; rm -f "$TMPIDX"
trap 'rm -f "$TMPIDX"' EXIT
GIT_INDEX_FILE="$TMPIDX" git --work-tree=dist add -A -f .
TREE="$(GIT_INDEX_FILE="$TMPIDX" git write-tree)"
COMMIT="$(git commit-tree "$TREE" -m "Deploy $(git rev-parse --short HEAD) $(date -u +%FT%TZ)")"
git push -f origin "${COMMIT}:refs/heads/gh-pages"

echo "== ensure GitHub Pages (source gh-pages /, custom domain ${DOMAIN})"
gh_api() {  # method path [json]; prints HTTP status, body -> /tmp/gh_api_body.json. Token is sent via stdin header, not argv.
  local data=(); [ $# -ge 3 ] && data=(--data "$3")
  printf 'Authorization: Bearer %s\n' "$GITHUB_TOKEN_CAMPSITES" | curl -sS -o /tmp/gh_api_body.json -w '%{http_code}' \
    -X "$1" -H @- -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "${data[@]}" "${API}$2"
}
BODY="{\"cname\":\"${DOMAIN}\",\"source\":{\"branch\":\"gh-pages\",\"path\":\"/\"}}"
ST="$(gh_api GET /pages)"
if [ "$ST" = 200 ]; then
  ST="$(gh_api PUT /pages "$BODY")"; echo "PUT /pages -> $ST"
  [ "$ST" = 204 ] || { cat /tmp/gh_api_body.json; exit 1; }
elif [ "$ST" = 404 ]; then
  ST="$(gh_api POST /pages "$BODY")"; echo "POST /pages -> $ST"
  [ "$ST" = 201 ] || { cat /tmp/gh_api_body.json; exit 1; }
else
  echo "GET /pages -> $ST"; cat /tmp/gh_api_body.json; exit 1
fi
ST="$(gh_api POST /pages/builds)"; echo "request Pages build -> $ST"
# Enforce HTTPS (non-fatal: GitHub refuses until DNS is verified and the Let's Encrypt cert is issued)
gh_api GET /pages >/dev/null
if python3 -c 'import json,sys; sys.exit(0 if json.load(open("/tmp/gh_api_body.json")).get("https_enforced") else 1)'; then
  echo "HTTPS enforced: yes"
else
  ST="$(gh_api PUT /pages "{\"cname\":\"${DOMAIN}\",\"https_enforced\":true,\"source\":{\"branch\":\"gh-pages\",\"path\":\"/\"}}")"
  echo "enforce HTTPS -> $ST (non-204 = certificate not ready yet; rerun later)"
fi
echo "== done: ${BASE_URL}/"
