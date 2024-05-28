#!/bin/bash

export WORK_DIR=$(dirname $(dirname $0))
export GCLOUD_PROJECT=$(gcloud config get project)
export GCLOUD_PROJECT_NUMBER=$(gcloud projects describe $GCLOUD_PROJECT --format="value(projectNumber)")
export REGION=asia-southeast1
export SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="email ~ ^trading-strategy" --format='value(email)')
export RUN_NAME=datasource
export SRC=$(mktemp -d)
export IMAGE=gcr.io/$GCLOUD_PROJECT/$RUN_NAME

echo "Project ID: $GCLOUD_PROJECT"
echo "Project Number: $GCLOUD_PROJECT_NUMBER"
echo "Cloud Run Name: $RUN_NAME"
read -p "Press enter to continue"

(cd $WORK_DIR && cp -r src/. .gcloudignore cloudbuild.yml $SRC)
echo "Copying source to $SRC... done!"
ls -la $SRC

if [ -z "$GIT_SSH_KEY" ]; then
    echo "WARN: Build variable not found 'GIT_SSH_KEY' !"
fi

echo "Build Image $IMAGE..."
(cd $SRC && gcloud builds submit $SRC \
    --config cloudbuild.yml \
    --substitutions "_IMAGE=$IMAGE,_PORT=8080,_GIT_SSH_KEY=$GIT_SSH_KEY")

echo "Deploy Cloud Run $RUN_NAME..."
gcloud run deploy $RUN_NAME \
    --image $IMAGE \
    --region $REGION \
    --project $GCLOUD_PROJECT \
    --no-allow-unauthenticated \
    --memory 1024Mi \
    --platform managed \
    --timeout 60m \
    --set-env-vars "GCLOUD_PROJECT=$GCLOUD_PROJECT" \
    --set-env-vars "GCLOUD_PROJECT_NUMBER=$GCLOUD_PROJECT_NUMBER" \
    --service-account $SERVICE_ACCOUNT

export SCHEDULER_NAME=$(gcloud scheduler jobs describe $RUN_NAME --region $REGION --format='value(name)')

if [ -z "$SCHEDULER_NAME" ]; then
    export SERVICE_URL=$(gcloud run services describe $RUN_NAME --platform managed --region $REGION --format 'value(status.url)')

    gcloud scheduler jobs create http $RUN_NAME-news-crawl \
        --location $REGION \
        --schedule '0 * * * *' \
        --time-zone America/Chicago \
        --uri="$SERVICE_URL/v1/news/crawl-to-db?source=SeekingAlpha" \
        --http-method GET \
        --attempt-deadline 30m \
        --oidc-service-account-email $SERVICE_ACCOUNT

    gcloud scheduler jobs create http $RUN_NAME-tick-data-download \
        --location $REGION \
        --schedule '0 * * * *' \
        --time-zone America/Chicago \
        --uri="$SERVICE_URL/v1/tick_data/download_files_background?workers_no=4" \
        --http-method GET \
        --attempt-deadline 30m \
        --oidc-service-account-email $SERVICE_ACCOUNT
fi
