#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

docker run --rm -ti \
    -u `id -u`:`id -g` \
    -v ${SCRIPT_DIR}/..:/home/user/introcp \
    -w /home/user/introcp \
    --ipc=host --cap-add=SYS_ADMIN --init \
    --name introcp \
    ercoppa/introcp \
    bash -c ". ~/.venv/bin/activate; bash scripts/run.sh ${1}"