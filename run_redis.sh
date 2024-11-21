#!/bin/bash

docker run -d \
  --name redis-server \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:latest redis-server --appendonly yes