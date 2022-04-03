#!/bin/bash

set -e

cat DIFF_IMAGES.txt | while read image_folder; do
    version=$(cat "./images/$image_folder/VERSION")
    image_tag="${CONTAINER_IMAGE_REGISTRY}/"${image_folder}":rc"
    docker build -t "$image_tag" "./images/${image_folder}"
    docker push "$image_tag"
done
