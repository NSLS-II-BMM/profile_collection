#!/bin/bash

export AZURE_TESTING=1

sudo apt-get update && sudo apt-get install redis

sudo systemctl status redis
sudo systemctl start redis
sudo systemctl status redis

if [ "$CONDA_ENV_NAME" == "collection-2021-1.0" ]; then
    conda remove wxpython --force -y
fi

