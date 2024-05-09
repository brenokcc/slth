#!/bin/sh
touch local.env
docker compose --progress plain up -d app --build