#!/bin/sh
touch local.env
docker-compose -p "${1:-test}-$(basename $PWD)" up tester --build --exit-code-from tester