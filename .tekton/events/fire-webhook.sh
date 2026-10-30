#!/usr/bin/env bash
#
# Fire a GitHub-shaped, HMAC-signed push webhook at the Customers EventListener.
#
# Use this to prove the Trigger starts a PipelineRun without waiting for a real
# GitHub delivery (e.g. from a laptop that GitHub cannot reach).
#
# Usage:
#   EVENTLISTENER_URL=http://localhost:8080 \
#   WEBHOOK_SECRET=<same value as the github-webhook-secret Secret> \
#   ./.tekton/events/fire-webhook.sh
#
# Optional overrides:
#   REPO_URL   clone URL put in the payload (default: this repo)
#   REF        git ref to simulate (default: refs/heads/master)
#   REVISION   commit sha to build (default: origin/master)
#
set -euo pipefail

EVENTLISTENER_URL="${EVENTLISTENER_URL:?set EVENTLISTENER_URL (Route URL or http://localhost:8080)}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:?set WEBHOOK_SECRET to the github-webhook-secret secretToken value}"
REPO_URL="${REPO_URL:-https://github.com/CSCI-GA-2820-FA26-001/customers.git}"
REF="${REF:-refs/heads/master}"
REVISION="${REVISION:-$(git rev-parse origin/master 2>/dev/null || echo master)}"

payload=$(cat <<JSON
{
  "ref": "${REF}",
  "after": "${REVISION}",
  "repository": {
    "clone_url": "${REPO_URL}"
  },
  "head_commit": {
    "id": "${REVISION}"
  }
}
JSON
)

# GitHub signs the raw body with HMAC-SHA256 and sends it as sha256=<hex>.
signature="sha256=$(printf '%s' "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $NF}')"
delivery="$(uuidgen 2>/dev/null || echo "local-$(date +%s)")"

echo "POST ${EVENTLISTENER_URL}"
echo "  X-GitHub-Event: push"
echo "  ref:            ${REF}"
echo "  after:          ${REVISION}"
echo

curl --silent --show-error \
  -X POST "${EVENTLISTENER_URL}" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: ${delivery}" \
  -H "X-Hub-Signature-256: ${signature}" \
  --data-binary "${payload}" \
  -w '\nHTTP %{http_code}\n'
