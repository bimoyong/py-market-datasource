#!/bin/bash

export WORK_DIR=$(dirname $(dirname $(realpath $0)))

[ -f $WORK_DIR/.env ] && source $WORK_DIR/.env
echo "Ingest environment variables done!"

if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    export GCLOUD_PROJECT=$(jq -r .project_id $GOOGLE_APPLICATION_CREDENTIALS)
else
    export GCLOUD_PROJECT=$(gcloud config get project)
fi

docker compose -f $WORK_DIR/docker-compose.yml up -d
