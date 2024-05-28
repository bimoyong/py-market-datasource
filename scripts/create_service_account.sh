#!/bin/bash

export GCLOUD_PROJECT=$(gcloud config get project)
export REGION=asia-southeast1
export SERVICE_ACCOUNT_NAME=trading-strategy

export SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter="email ~ ^$SERVICE_ACCOUNT_NAME" \
    --format='value(email)')

if [ -z "$SERVICE_ACCOUNT" ]; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name 'Trading Strategy' \
        --project=$GCLOUD_PROJECT >/dev/null
fi

export SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter="email ~ ^$SERVICE_ACCOUNT_NAME" \
    --format='value(email)')

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/run.invoker' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/secretmanager.secretAccessor' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/bigquery.dataEditor' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/bigquery.jobUser' >/dev/null

gcloud projects add-iam-policy-binding $GCLOUD_PROJECT \
    --member serviceAccount:$SERVICE_ACCOUNT \
    --role 'roles/storage.admin' >/dev/null

echo $SERVICE_ACCOUNT
