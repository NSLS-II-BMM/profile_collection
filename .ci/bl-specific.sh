#!/bin/bash

export AZURE_TESTING=1

sudo apt-get update && sudo apt-get install redis

sudo systemctl status redis
sudo systemctl start redis
sudo systemctl status redis

