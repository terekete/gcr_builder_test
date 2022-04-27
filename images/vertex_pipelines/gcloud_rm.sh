#!/bin/bash

echo "removing the temp pipelines folder"
echo "All arguments: $0"
echo "Project name: $1"
echo "uuid: $2"

cd ..

rm -rf pipelines$2

ls -la

echo "temp pipelines folder removed"
