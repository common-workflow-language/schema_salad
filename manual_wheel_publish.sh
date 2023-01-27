#!/bin/sh
# call with your GitHub personal access token, with at least "repo" permissions
# and the target version tag
curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $1"\
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/common-workflow-language/schema_salad/dispatches \
  -d "{\"event_type\":\"on-demand-wheel\",\"client_payload\":{\"ref\":\"$2\", \"publish_wheel\": true}}"
