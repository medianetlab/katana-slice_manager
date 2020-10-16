#!/bin/bash

# Push docker images to docker hub

# Login to docker account
export docker_pass=${1}
export major_release=${2}

docker login -u mnlab -p "$docker_pass"

# Create the tag images
docker image tag katana-mngr mnlab/katana-mngr:"${major_release}.${BUILD_NUMBER}"
docker image tag katana-cli mnlab/katana-cli:"${major_release}.${BUILD_NUMBER}"
docker image tag katana-nbi mnlab/katana-nbi:"${major_release}.${BUILD_NUMBER}"
docker image tag katana-nfv_mon mnlab/katana-nfv_mon:"${major_release}.${BUILD_NUMBER}"

# Push to the remote Docker Hub
docker image push mnlab/katana-mngr:"${major_release}.${BUILD_NUMBER}"
docker image push mnlab/katana-clir:"${major_release}.${BUILD_NUMBER}"
docker image push mnlab/katana-nbi:"${major_release}.${BUILD_NUMBER}"
docker image push mnlab/katana-nfv_mon:"${major_release}.${BUILD_NUMBER}"