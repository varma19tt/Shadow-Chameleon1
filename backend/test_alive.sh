#!/bin/bash
# build and run container in background
docker build -t sc-backend-test .
CID=$(docker run -d -p 8000:8000 sc-backend-test)
sleep 2
curl -sS http://127.0.0.1:8000/alive || true
docker rm -f $CID
