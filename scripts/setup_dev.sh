#!/bin/bash

gcloud auth application-default login

source .env

export GCLOUD_PROJECT=$(gcloud config get project)
export GCLOUD_PROJECT_NUMBER=$(gcloud projects describe $GCLOUD_PROJECT --format="value(projectNumber)")

docker compose -f docker-compose.yml up -d
