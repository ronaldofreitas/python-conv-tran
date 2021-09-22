#!/bin/bash

docker rmi $(docker images -f "dangling=true" -q) -f 2>/dev/null || echo "não existem imagens <none>."

exit 0