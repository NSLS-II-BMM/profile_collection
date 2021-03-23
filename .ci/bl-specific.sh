#!/bin/bash

sudo apt-get update && sudo apt-get install redis

sudo systemctl status redis
sudo systemctl start redis
sudo systemctl status redis

