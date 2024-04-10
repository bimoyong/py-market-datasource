#!/bin/bash

export GCLOUD_PROJECT=$(gcloud config get project)
export GCLOUD_PROJECT_NUMBER=$(gcloud projects describe $GCLOUD_PROJECT --format="value(projectNumber)")
export REGION=us-central1
export SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="email ~ ^trading-strategy" --format='value(email)')
export RUN_NAME=datasource
export SRC=$(mktemp -d)
export IMAGE=gcr.io/$GCLOUD_PROJECT/$RUN_NAME

echo "Project ID: $GCLOUD_PROJECT"
echo "Project Number: $GCLOUD_PROJECT_NUMBER"
echo "Cloud Run Name: $RUN_NAME"
read -p "Press enter to continue"

cp -r src/. .python-version Dockerfile Procfile requirements.txt $SRC
echo "Copying source to $SRC... done!"
ls -la $SRC

if [ -z "$GIT_SSH_KEY" ]; then
    echo "WARN: Build variable not found 'GIT_SSH_KEY' !"
fi

echo "Build Image $IMAGE..."
gcloud builds submit $SRC \
    --config cloudbuild.yml \
    --region $REGION \
    --substitutions "_IMAGE=$IMAGE,_PORT=8080,_GIT_SSH_KEY=$GIT_SSH_KEY"

echo "Deploy Cloud Run $RUN_NAME..."
gcloud run deploy $RUN_NAME \
    --image $IMAGE \
    --region $REGION \
    --project $GCLOUD_PROJECT \
    --no-allow-unauthenticated \
    --memory 128Mi \
    --platform managed \
    --timeout 1m \
    --set-env-vars "GCLOUD_PROJECT=$GCLOUD_PROJECT" \
    --set-env-vars "GCLOUD_PROJECT_NUMBER=$GCLOUD_PROJECT_NUMBER" \
    --service-account $SERVICE_ACCOUNT
