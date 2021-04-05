#!/bin/bash

export AZURE_TESTING=1

if [ "$CONDA_ENV_NAME" == "collection-2021-1.0" ]; then
    conda remove wxpython --force -y
fi

