#!/bin/bash

set -e

# cat DIFF_IMAGES.txt | while read image_folder; do
#     version=$(cat "./images/$image_folder/VERSION")
#     image_tag="${CONTAINER_IMAGE_REGISTRY}/ai-platform/"${image_folder}":rc"
#     docker build -t "$image_tag" "./images/${image_folder}"
#     docker push "$image_tag"
# done

curl -L -o ds.tar.gz https://downloads.dockerslim.com/releases/1.37.4/dist_linux.tar.gz
tar -xvf ds.tar.gz
mv dist_linux/docker-slim /usr/local/bin
mv dist_linux/docker-slim-sensor /usr/local/bin/
docker-slim update

cat DIFF_IMAGES.txt | while read image_folder; do
    version=$(cat "./images/$image_folder/VERSION")
    image_tag="${CONTAINER_IMAGE_REGISTRY}/"${image_folder}":${version}-rc"
    slim_image_tag="${CONTAINER_IMAGE_REGISTRY}/"${image_folder}":slim-rc"
    docker-slim build --include-path /opt --include-path /usr --include-path /etc --include-shell --copy-meta-artifacts --show-blogs --dockerfile Dockerfile --sensor-ipc-mode proxy --sensor-ipc-endpoint $(docker network inspect bridge -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}' | cut -f1) --http-probe=false --tag ${slim_image_tag} "./images/${image_folder}/" </dev/null
    cat slim.report.json
    docker push "$slim_image_tag"
done
