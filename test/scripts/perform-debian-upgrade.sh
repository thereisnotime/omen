#!/bin/bash

PERFORM_UPGRADE=${1:-"true"}
export DEBIAN_FRONTEND=noninteractive
export DEBIAN_PRIORITY=critical

# Suppress PostgreSQL upgrade prompts
debconf-set-selections <<EOF
postgresql-common  postgresql-common/obsolete-major   boolean true
EOF

# Fix dpkg lock issue
sudo rm -rf /var/lib/dpkg/lock-frontend
sudo rm -rf /var/cache/apt/archives/lock
sudo dpkg --configure -a


if [ -x "$(command -v sudo)" ]; then
    sudo apt-get update -y
    if [ "$PERFORM_UPGRADE" == "true" ]; then
        sudo apt-get upgrade -y -qq
        sudo apt-get dist-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
    fi
else
    if [ "$(id -u)" -ne 0 ]; then
        echo "Please run as root"
        exit 1
    fi
    apt-get update -y
    if [ "$PERFORM_UPGRADE" == "true" ]; then
        apt -get upgrade -y -qq
        apt-get dist-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"
    fi 
fi