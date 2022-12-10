# jt-ssh-client
SSH Client

<img src="https://img.shields.io/badge/license-MIT-blue.svg"></a>

### Client Side (PC/MAC)

1. Python v3.10.4 or greater
2. PIP v22.0.4 or greater
3. SSH private and public key (RSA / DSA / ECDSA)

### Server Side (Android Devices)

1. SimpleSSHD - [Play Store](https://play.google.com/store/apps/details?id=org.galexander.sshd)
2. Any SSH Daemon/Server on your Android devices

### Server Side (Linux Devices)

1. Any SSH Daemon/Server on your Linux devices

# Usage

### Client Side (PC/MAC/LINUX)

*_If you already possess a valid SSH private and public key pair (RSA, DSA or ECDSA), you can skip directly to Step 2_

1. Create an SSH private and public key pair on your desktop/laptop (RSA, DSA or ECDSA).
2. Create a Python virtual environment and install all dependent libraries
3. Invoke your code to connect and manipulate your devices via SSH/SCP/SFTP

#### Step 1
```sh
#!/bin/bash
# Create an SSH private and public key pair. You may skip this step
# if you already possess a valid SSH private and public key pair.

# Replace the placeholder values (Anything enclosed by the "<" and 
# ">" characters) accordingly. Examples are shown further below:

$ ssh-keygen -t <key_type>

# Examples:

# $ ssh-keygen -t dsa
# $ ssh-keygen -t rsa
# $ ssh-keygen -t ecdsa
```

#### Step 2
```sh
#!/bin/bash
# Create a Python virtual environment

$ cd jt-ssh-client
$ python3 -m venv .env
$ source .env/bin/activate

# Install library dependencies

$ pip3 install wheel --no-cache-dir
$ pip3 install -r requirements.txt --no-cache-dir
$ pip3 install -e .
```

### Server Side (Android Device)

*_The following instructions assumes that you're running SimpleSSHD on your Android devices_

1. Launch SimpleSSHD and delete existing authorized keys
2. Restart SimpleSSHD and copy the SSH public key from client to server

#### Step 2
```sh
#!/bin/bash

# Deploy your SSH public key to your Android devices. Note, the 
# following command below is applicable if you're using SimpleSSHD 
# however, if you're using other available SSH Daemon/Server service,
# then please deploy your SSH public key per-documentation or 
# recommended methodology.

# Replace the placeholder values (Anything enclosed by the "<" and 
# ">" characters) accordingly. Examples are shown further below:

$ cat <ssh_public_key> | ssh <hostname/ip_address> -p <port_number> "cat >> /data/user/0/org.galexander.sshd/files/authorized_keys"

# Examples: 

# $ cat id_dsa.pub | ssh 192.168.1.70 -p 22 "cat >> /data/user/0/org.galexander.sshd/files/authorized_keys"
# $ cat id_rsa.pub | ssh android.phone.local -p 3000 "cat >> /data/user/0/org.galexander.sshd/files/authorized_keys"
# $ cat id_ed25519.pub | ssh 192.168.5.35 -p 22 "cat >> /data/user/0/org.galexander.sshd/files/authorized_keys"
```

# Development

Clone the repository and setup your environment for development

_Linux (Ubuntu/Debian)_

```shell
#!/bin/bash
# Create a Python virtual environment

$ cd jt-ssh-client
$ python3 -m venv .env
$ source .env/bin/activate

# Install library dependencies

$ pip3 install wheel --no-cache-dir
$ pip3 install -r requirements.txt --no-cache-dir
$ pip3 install -e .
```
