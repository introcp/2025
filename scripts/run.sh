#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

ls ${1} | entr -rn bash ${SCRIPT_DIR}/process.sh ${1}
