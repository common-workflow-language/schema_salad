#!/bin/sh

# Usage:
# ./manual_wheel_publish.sh target_version_tag

# set GITHUB_TOKEN to your personal access token, with at least "repo" permissions
# and CIRCLE_TOKEN with your CircleCI token: https://app.circleci.com/settings/user/tokens
curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}"\
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/common-workflow-language/schema_salad/dispatches \
  -d "{\"event_type\":\"on-demand-wheel\",\"client_payload\":{\"ref\":\"$1\", \"publish_wheel\": true}}"

curl -X POST --header "Content-Type: application/json" --header "Circle-Token: $CIRCLE_TOKEN" -d "{
  \"parameters\": {
    \"REF\": \"$1\"
  }
}" https://circleci.com/api/v2/project/github/common-workflow-language/schema_salad/pipeline
