#!/bin/bash

set -e

# cat DIFF_IMAGES.txt | while read image_folder; do
#     version=$(cat "./images/$image_folder/VERSION")
#     old_image_tag="${CONTAINER_IMAGE_REGISTRY}/ai-platform/"${image_folder}":rc"
#     new_image_tag="${CONTAINER_IMAGE_REGISTRY}/ai-platform/"${image_folder}":${version}"
#     latest_image_tag="${CONTAINER_IMAGE_REGISTRY}/ai-platform/"${image_folder}":latest"
#     gcloud container images add-tag "${old_image_tag}" "${new_image_tag}" "${latest_image_tag}" --quiet
# done

cat DIFF_IMAGES.txt | while read img_folder; do
    version=$(cat "./images/${img_folder}/VERSION")
    slim_img_tag=${CONTAINER_IMAGE_REGISTRY}"/"${img_folder}":slim-rc"
    latest_img_tag=${CONTAINER_IMAGE_REGISTRY}"/"${img_folder}":latest"
    gcloud artifacts docker tags add "${slim_img_tag}" "${latest_img_tag}" --quiet
    echo "  Release Image URI:         " ${latest_img_tag}
done
