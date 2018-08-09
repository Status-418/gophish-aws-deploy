#!/bin/bash

# Getting some dependancies installed
sudo apt-get update
sudo apt-get install -y golang-go unzip git

# Pulling down goPhish, unpacking and configuring goPhish
wget https://github.com/gophish/gophish/releases/download/v0.6.0/gophish-v0.6.0-linux-64bit.zip
unzip gophish-v0.6.0-linux-64bit.zip -d /opt/gophish
ln -s /opt/gophish-v0.6-linux-64bit/ /opt/gophish
sed -i 's!127.0.0.1!0.0.0.0!g' /opt/gophish/config.json
chmod +x /opt/gophish/gophish
openssl req -newkey rsa:2048 -nodes -keyout /opt/gophish/gophish_admin.key -x509 -days 365 -out /opt/gophish/gophish_admin.crt -batch -subj "C=US/CN=gophish.example.com"
