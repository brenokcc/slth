#!/bin/sh
touch local.env
docker-compose --progress plain --env-file base.env --env-file local.env up frontend backend --build