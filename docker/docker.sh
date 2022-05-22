#!/usr/bin/env bash

LATEST_VERSION=3.1.0
REPOSITORY="interlegis"

docker build --no-cache -t $REPOSITORY/saap:$LATEST_VERSION .

docker tag $REPOSITORY/saap:$LATEST_VERSION $REPOSITORY/saap:latest

docker push $REPOSITORY/saap:$LATEST_VERSION
docker push $REPOSITORY/saap:latest
