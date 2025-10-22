# Test Environment

This is a simple test environment with Ubuntu 22.04 VM. 

## Pre-Requisites

Vagrant, Virtualbox and the vagrant-vbguest plugin are required. Recommended is a markdown execution addon for VSCode so that you can use the README.md as a runbook.

```bash
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update
sudo apt-get install -y vagrant
vagrant plugin install vagrant-vbguest vagrant-disksize
```

Prepare a test keypair used for automation purposes:

```bash
yes | ssh-keygen -t ed25519 -C "ansible@omen" -f test/key -N "Temporary master key for testing purposes."
chmod 600 test/key
chmod 644 test/key.pub
```

## Configuration

```bash
cd test || true
export VM_CPU_COUNT=4
export VM_MEMORY_SIZE=16384
export VM_NAME="TEST-OMEN-UBUNTU2204"
export VM_BOX="ubuntu/jammy64"
export VM_IMAGE_VERSION="20241002.0.0"
export VM_DISK_LOCATION="$HOME/VMs/TEST-OMEN-UBUNTU2204"
export VM_BRIDGE_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n 1)
export VM_DESCRIPTION="Managed by Vagrant in omen/test/ ($(pwd))"
export PROJECT_FOLDER="$(pwd)/shared"
export ALLOWED_PUBLIC_KEYS="$(cat key.pub)"
```

## Runbook

Start the VM:

```bash
vagrant up
```

Connect to the VM:

```bash
vagrant ssh
```

Get VM Internal IP:

```bash
vagrant ssh -c "hostname -I"
```

Stop the VM:

```bash
vagrant halt
```

Create snapshot:

```bash
vagrant snapshot save snapshot01
```

Restore snapshot:

```bash
vagrant snapshot restore snapshot01
```

Destroy:

```bash
vagrant destroy -f
```

Cleanup:

```bash
vagrant snapshot delete snapshot01 || true
vagrant destroy -f && \
rm -rf .vagrant
if [[ -d "${VM_DISK_LOCATION:-}" ]]; then
  if find "$VM_DISK_LOCATION" -maxdepth 2 -type f -name '*.vbox' -print -quit | grep -q .; then
    echo "Removing VM disk location contents: $VM_DISK_LOCATION"
    rm -rf -- "$VM_DISK_LOCATION"/*
  else
    echo "WARNING: No .vbox file found in '$VM_DISK_LOCATION'; refusing to delete."
  fi
else
  echo "WARNING: VM_DISK_LOCATION is invalid or not a directory: '${VM_DISK_LOCATION:-unset}'"
fi
```
