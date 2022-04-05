#!/bin/sh

set -e
export team=${TEAM}
export project=${PROJECT_ID}
export state_bucket=${STATE_BUCKET}
export project_type=${PROJECT_TYPE}
export build_sa=${BUILD_SA}
export PULUMI_CONFIG_PASSPHRASE=/secret/passphrase
pulumi login ${STATE_BUCKET}

echo "TEAM: ${team}"
echo "PROJECT: ${project}"
echo "STATE: ${state_bucket}"
echo "PROJECT TYPE: ${project_type}"
echo "BUILD SA: ${build_sa}"
python /main.py $team $project $project_type $build_sa
