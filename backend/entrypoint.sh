#!/bin/sh
set -e

# Get a fresh access token via Universal Auth on every container startup.
# INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET must be set in the environment.
: "${INFISICAL_CLIENT_ID:?INFISICAL_CLIENT_ID is required}"
: "${INFISICAL_CLIENT_SECRET:?INFISICAL_CLIENT_SECRET is required}"

INFISICAL_DOMAIN=${INFISICAL_DOMAIN:-https://secrets.drose.io}
INFISICAL_AUTH_MAX_ATTEMPTS=${INFISICAL_AUTH_MAX_ATTEMPTS:-36}
INFISICAL_AUTH_RETRY_SECONDS=${INFISICAL_AUTH_RETRY_SECONDS:-5}
attempt=1

while [ "$attempt" -le "$INFISICAL_AUTH_MAX_ATTEMPTS" ]; do
  response=""
  token=""

  if response=$(curl -fsS -X POST "$INFISICAL_DOMAIN/api/v1/auth/universal-auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"clientId\":\"${INFISICAL_CLIENT_ID}\",\"clientSecret\":\"${INFISICAL_CLIENT_SECRET}\"}"); then
    token=$(printf "%s" "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("accessToken", ""))' 2>/dev/null || true)
  fi

  if [ -n "$token" ]; then
    INFISICAL_TOKEN=$token
    export INFISICAL_TOKEN
    break
  fi

  if [ "$attempt" -eq "$INFISICAL_AUTH_MAX_ATTEMPTS" ]; then
    echo "Infisical authentication unavailable after $attempt attempts" >&2
    exit 1
  fi

  echo "Infisical authentication unavailable (attempt $attempt/$INFISICAL_AUTH_MAX_ATTEMPTS); retrying" >&2
  attempt=$((attempt + 1))
  sleep "$INFISICAL_AUTH_RETRY_SECONDS"
done

exec infisical run \
  --env "${INFISICAL_ENV:-prod}" \
  --domain "$INFISICAL_DOMAIN" \
  --projectId "fdc5cddf-0304-448e-ba40-7cace6062dab" \
  -- "$@"
