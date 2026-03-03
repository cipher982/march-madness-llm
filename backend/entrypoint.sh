#!/bin/sh
set -e

# Get a fresh access token via Universal Auth on every container startup.
# INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET must be set in the environment.
INFISICAL_TOKEN=$(curl -sf -X POST "https://secrets.drose.io/api/v1/auth/universal-auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"clientId\":\"${INFISICAL_CLIENT_ID}\",\"clientSecret\":\"${INFISICAL_CLIENT_SECRET}\"}" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['accessToken'])")
export INFISICAL_TOKEN

exec infisical run \
  --env "${INFISICAL_ENV:-prod}" \
  --domain "https://secrets.drose.io" \
  --projectId "fdc5cddf-0304-448e-ba40-7cace6062dab" \
  -- "$@"
