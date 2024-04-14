#!/bin/sh
touch local.env
docker-compose -p "${1:-test}-$(basename $PWD)" up selenium frontend tester --build --exit-code-from tester
docker-compose -p "${1:-test}-$(basename $PWD)" down