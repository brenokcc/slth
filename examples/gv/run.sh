#!/bin/sh
touch local.env
docker compose --progress up -d app --build