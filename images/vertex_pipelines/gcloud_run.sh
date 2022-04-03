#!/bin/bash

echo "All arguments: $0"
echo "Project name: $1"
echo "uuid: $2"

# rm -rf pipelines$2
mkdir -p pipelines$2

cd pipelines$2

gsutil -m cp -r gs://$1-vertex-scripts/vertex_pipelines/* .

ls -lR
