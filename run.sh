#!/bin/sh
touch local.env
docker-compose up backend postgres --build