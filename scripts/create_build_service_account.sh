#!/bin/bash

export WORK_DIR=$(dirname $(dirname $(realpath $0)))

[ -f .env ] && source .env

export GCLOUD_PROJECT=$(gcloud config get project)
export SERVICE_ACCOUNT_NAME=dev-builder
export SERVICE_ACCOUNT_DISPLAY_NAME=Development Builder

export SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter="email ~ ^$SERVICE_ACCOUNT_NAME" \
    --format='value(email)')

if [ -z "$SERVICE_ACCOUNT" ]; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name $SERVICE_ACCOUNT_DISPLAY_NAME \
        --project=$GCLOUD_PROJECT >/dev/null
fi

export SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter="email ~ ^$SERVICE_ACCOUNT_NAME" \
    --format='value(email)')

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/run.developer' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/run.sourceDeveloper' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/iam.serviceAccountUser' >/dev/null

echo $SERVICE_ACCOUNT
