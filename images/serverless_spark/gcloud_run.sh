#!/bin/bash

echo "All arguments: $0"
echo "Project name: $1"
echo "Script name: $2"
echo "Custom_image_path: $3"
echo "Bucket: $4"

# gsutil ls gs://$1-spark-scripts/pyspark_jobs/$2

if [ $3 = "default" ]; then
    echo default container
    gcloud beta dataproc batches submit pyspark \
        --region northamerica-northeast1 \
        --tags spark \
        --subnet projects/$1/regions/northamerica-northeast1/subnetworks/spark-subnet-pr \
        --service-account bilayer-sa@$1.iam.gserviceaccount.com \
        --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.23.2.jar \
        gs://$1-spark-scripts/pyspark_jobs/$2 -- $1 $4
else
    echo custom container
    gcloud beta dataproc batches submit pyspark \
        --region northamerica-northeast1 \
        --container-image $3 \
        --tags spark \
        --subnet projects/$1/regions/northamerica-northeast1/subnetworks/spark-subnet-pr \
        --service-account bilayer-sa@$1.iam.gserviceaccount.com \
        gs://$1-spark-scripts/pyspark_jobs/$2 -- $1 $4
fi
