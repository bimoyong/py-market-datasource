#!/bin/bash

export WORK_DIR=$(dirname $(dirname $(realpath $0)))

[ -f $WORK_DIR/.env ] && source $WORK_DIR/.env
echo "Ingest environment variables done!"

export GCLOUD_PROJECT=$(gcloud config get project)
export GCLOUD_PROJECT_NUMBER=$(gcloud projects describe $GCLOUD_PROJECT --format="value(projectNumber)")
export SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="email ~ ^trading-strategy" --format='value(email)')
export SRC=$(mktemp -d)
export IMAGE=gcr.io/$GCLOUD_PROJECT/$RUN_NAME

echo "Project ID: $GCLOUD_PROJECT"
echo "Project Number: $GCLOUD_PROJECT_NUMBER"
echo "Cloud Run Name: $RUN_NAME"

read -p "Press enter to continue"

(cd $WORK_DIR && cp -r \
    src/. \
    .gcloudignore \
    cloudbuild.yml \
    $SRC)
echo "Copying source to $SRC... done!"
ls -la $SRC

if [ -z "$GIT_SSH_KEY" ]; then
    echo "WARN: Build variable not found 'GIT_SSH_KEY' !"
fi

echo "Build Image $IMAGE..."
(cd $SRC && gcloud builds submit $SRC \
    --region $GCLOUD_REGION \
    --config cloudbuild.yml \
    --substitutions "_IMAGE=$IMAGE,_PORT=8080,_GIT_SSH_KEY=$GIT_SSH_KEY")

echo "Deploy Cloud Run $RUN_NAME..."
gcloud run deploy $RUN_NAME \
    --image $IMAGE \
    --region $GCLOUD_REGION \
    --project $GCLOUD_PROJECT \
    --no-allow-unauthenticated \
    --memory 4096Mi \
    --platform managed \
    --timeout 60m \
    --set-env-vars "GCLOUD_PROJECT=$GCLOUD_PROJECT" \
    --set-env-vars "GCLOUD_PROJECT_NUMBER=$GCLOUD_PROJECT_NUMBER" \
    --service-account $SERVICE_ACCOUNT

export SERVICE_URL=$(gcloud run services describe $RUN_NAME --platform managed --region $GCLOUD_REGION --format 'value(status.url)')

SCHEDULER_NAME=$RUN_NAME-news-crawl
if gcloud scheduler jobs update http $SCHEDULER_NAME \
    --location $GCLOUD_REGION \
    --schedule '0 * * * *' \
    --time-zone America/Chicago \
    --uri="$SERVICE_URL/v1/news/crawl-to-db?source=SeekingAlpha" \
    --http-method GET \
    --attempt-deadline 30m \
    --oidc-service-account-email $SERVICE_ACCOUNT; then

    echo "Updated Scheduler $SCHEDULER_NAME successfully."
else
    gcloud scheduler jobs create http $SCHEDULER_NAME \
        --location $GCLOUD_REGION \
        --schedule '0 * * * *' \
        --time-zone America/Chicago \
        --uri="$SERVICE_URL/v1/news/crawl-to-db?source=SeekingAlpha" \
        --http-method GET \
        --attempt-deadline 30m \
        --oidc-service-account-email $SERVICE_ACCOUNT

    echo "Scheduler $JOB_NAME does not exist. Creating a new Scheduler..."
fi

# SCHEDULER_NAME=$RUN_NAME-tick-data-download
# if gcloud scheduler jobs update http $SCHEDULER_NAME \
#     --location $GCLOUD_REGION \
#     --schedule '0 * * * *' \
#     --time-zone America/Chicago \
#     --uri="$SERVICE_URL/v1/tick_data/download_files_background?workers_no=8" \
#     --http-method GET \
#     --attempt-deadline 30m \
#     --oidc-service-account-email $SERVICE_ACCOUNT; then

#     echo "Updated Scheduler $SCHEDULER_NAME successfully."
# else
#     gcloud scheduler jobs create http $SCHEDULER_NAME \
#         --location $GCLOUD_REGION \
#         --schedule '0 * * * *' \
#         --time-zone America/Chicago \
#         --uri="$SERVICE_URL/v1/tick_data/download_files_background?workers_no=8" \
#         --http-method GET \
#         --attempt-deadline 30m \
#         --oidc-service-account-email $SERVICE_ACCOUNT

#     echo "Scheduler $JOB_NAME does not exist. Creating a new Scheduler..."
# fi
