#!/bin/bash

# 正式用
CONTAINER="akasha-service"
DOCKER_REPO="iiicondor/$CONTAINER"
# HARBOR_REPO="harbor.arfa.wise-paas.com/ifp/$CONTAINER"
VERSION="1.0.0.5"
# MESSAGE="[Lisa]"
MESSAGE="[Vivian] add rerank"

docker build -t $DOCKER_REPO:$VERSION .
docker push $DOCKER_REPO:$VERSION
docker tag $DOCKER_REPO:$VERSION
# docker tag $HARBOR_REPO:$VERSION
# docker push $HARBOR_REPO:$VERSION

# 沒有windows版本
# # 使用 docker-slim 縮減映像大小
# docker-slim build --target $DOCKER_REPO:$VERSION --tag $DOCKER_REPO:slim-$VERSION

# # 推送縮減後的映像
# docker push $DOCKER_REPO:slim-$VERSION

echo "[`date "+%Y-%m-%d %H:%M:%S"`] $DOCKER_REPO:$VERSION => {$MESSAGE}" >> module/ImageInfo.txt
