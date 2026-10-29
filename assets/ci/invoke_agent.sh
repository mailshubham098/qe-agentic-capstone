#!/usr/bin/env bash
#
# invoke_agent.sh — call a QE agent workflow exposed by IBM ICA and write its
# response to an evidence file.
#
# WHY THIS EXISTS
#   IBM Bob is an agentic IDE: it authors assets on a Quality Engineer's
#   desktop. It is not a CI service and must not be called from a pipeline.
#   IBM ICA, by contrast, exposes a Langflow workflow as an HTTP/MCP endpoint,
#   which is what a pipeline can legitimately call. So:
#       Bob  -> authoring time (WF02..WF07, WF10 asset generation)
#       ICA  -> run time      (WF08, WF09, WF11..WF14 + release gate)
#   This script is the single place the pipeline talks to an agent.
#
# CONTRACT
#   Every agent in this capstone returns a JSON object containing at least:
#       { "verdict": "PASS" | "FAIL" | "WARN" | "ADVISORY",
#         "summary": "<one paragraph>",
#         "findings": [ ... ],
#         "evidence": [ ... ] }
#   The caller decides whether a verdict blocks. This script never decides.
#
# USAGE
#   ./invoke_agent.sh <workflow-name> <payload-file> <output-file>
#
# REQUIRED ENVIRONMENT (set as CI secrets — never commit these)
#   ICA_WORKFLOW_URL     Base URL of the exposed ICA workflow endpoint
#   ICA_GATEWAY_TOKEN    MCP Gateway bearer token
#   ICA_CONTEXT_KEY      Context Studio x-api-key
#   ICA_CONTEXT_ID       Context identifier (ctx_...)
#
# EXIT CODES
#   0  the agent replied and the response was written
#   1  usage error
#   2  missing configuration
#   3  transport failure after retries
#   4  the agent replied but the response was not parseable JSON
#
set -euo pipefail

WORKFLOW="${1:-}"
PAYLOAD_FILE="${2:-}"
OUTPUT_FILE="${3:-}"

if [[ -z "$WORKFLOW" || -z "$PAYLOAD_FILE" || -z "$OUTPUT_FILE" ]]; then
  echo "usage: $0 <workflow-name> <payload-file> <output-file>" >&2
  exit 1
fi

if [[ ! -f "$PAYLOAD_FILE" ]]; then
  echo "error: payload file not found: $PAYLOAD_FILE" >&2
  exit 1
fi

for var in ICA_WORKFLOW_URL ICA_GATEWAY_TOKEN ICA_CONTEXT_KEY ICA_CONTEXT_ID; do
  if [[ -z "${!var:-}" ]]; then
    echo "error: required environment variable $var is not set" >&2
    echo "hint: configure it as a CI secret; see doc 07 §3" >&2
    exit 2
  fi
done

mkdir -p "$(dirname "$OUTPUT_FILE")"

# The agent is grounded through the context, so context_id travels with every
# request. AgentPersona lets Control Tower attribute the trace to the caller.
REQUEST_BODY="$(mktemp)"
trap 'rm -f "$REQUEST_BODY"' EXIT

python3 - "$PAYLOAD_FILE" "$WORKFLOW" > "$REQUEST_BODY" <<'PY'
import json, os, sys
payload_file, workflow = sys.argv[1], sys.argv[2]
with open(payload_file, encoding="utf-8") as fh:
    raw = fh.read()
# A payload may be JSON already, or free text to hand to the supervisor.
try:
    inner = json.loads(raw)
except json.JSONDecodeError:
    inner = {"input": raw}
# ICA Agent Studio /chat API expects { "message": "..." }
# We serialise the full payload as the message string so the agent sees it.
message_text = json.dumps({"workflow": workflow,
                            "context_id": os.environ["ICA_CONTEXT_ID"],
                            "AgentPersona": "CIPipeline",
                            "payload": inner})
body = {"message": message_text}
json.dump(body, sys.stdout)
PY

ATTEMPTS=3
DELAY=10
HTTP_CODE=""

for attempt in $(seq 1 "$ATTEMPTS"); do
  echo "invoke_agent: calling '$WORKFLOW' (attempt $attempt/$ATTEMPTS)" >&2
  set +e
  HTTP_CODE="$(curl -sS \
    --max-time 300 \
    --connect-timeout 20 \
    -o "$OUTPUT_FILE" \
    -w '%{http_code}' \
    -X POST "${ICA_WORKFLOW_URL%/}" \
    -H "Authorization: Bearer ${ICA_GATEWAY_TOKEN}" \
    -H "x-api-key: ${ICA_CONTEXT_KEY}" \
    -H 'Content-Type: application/json' \
    --data-binary "@${REQUEST_BODY}")"
  CURL_RC=$?
  set -e

  if [[ $CURL_RC -eq 0 && "$HTTP_CODE" =~ ^2 ]]; then
    break
  fi

  echo "invoke_agent: attempt $attempt failed (curl rc=$CURL_RC http=$HTTP_CODE)" >&2
  if [[ $attempt -eq $ATTEMPTS ]]; then
    echo "error: agent '$WORKFLOW' unreachable after $ATTEMPTS attempts" >&2
    exit 3
  fi
  sleep "$DELAY"
  DELAY=$(( DELAY * 2 ))
done

# Validate and normalise. A blank or non-JSON body is a hard failure: a silent
# empty response must never be mistaken for a passing gate.
if ! python3 - "$OUTPUT_FILE" <<'PY'
import json, sys, pathlib
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
except Exception as exc:                      # noqa: BLE001
    print(f"error: agent response is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(1)
if not isinstance(data, dict):
    print("error: agent response was not a JSON object", file=sys.stderr)
    sys.exit(1)
# ICA Agent Studio wraps its reply in {"message": "<json string>"}
# Unwrap it so downstream pipeline steps see a consistent schema.
if "message" in data and "verdict" not in data:
    try:
        inner = json.loads(data["message"])
        if isinstance(inner, dict):
            data = inner
            pathlib.Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    except (json.JSONDecodeError, TypeError):
        pass  # leave as-is; downstream step will handle
verdict = data.get("verdict", "ADVISORY")
print(f"invoke_agent: verdict={verdict}", file=sys.stderr)
PY
then
  echo "error: unusable response from agent '$WORKFLOW' — see $OUTPUT_FILE" >&2
  exit 4
fi

echo "invoke_agent: response written to $OUTPUT_FILE" >&2
