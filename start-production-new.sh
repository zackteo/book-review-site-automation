#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install -y python3
sudo apt-get install -y python3-venv

#Programmaticatically edit yml
cd production_setup
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
python3 production.py

