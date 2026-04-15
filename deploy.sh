#!/bin/bash
# Build image txmit tanpa cache
mkdir logs
mkdir csv
chmod 777 logs
chmod 777 csv
docker-compose build --no-cache onlimo

# Start semua service di background
docker-compose up -d
