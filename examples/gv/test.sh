#!/bin/sh
touch local.env
docker-compose --progress plain -p "${1:-test}-$(basename $PWD)" up selenium tester --build --exit-code-from tester
docker-compose --progress plain -p "${1:-test}-$(basename $PWD)" down