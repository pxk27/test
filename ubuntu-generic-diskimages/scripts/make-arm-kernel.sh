#!/bin/bash

# Copyright (c) 2024 The Regents of the University of California.
# SPDX-License-Identifier: BSD 3-Clause

#installing packages

apt-get update
apt-get install -y fakeroot build-essential crash kexec-tools makedumpfile kernel-wedge
apt-get install -y scons
apt-get install -y git
apt-get install -y vim
apt-get install -y build-essential
# Fixing the sources.list file to include deb-src: https://askubuntu.com/questions/1512042/ubuntu-24-04-getting-error-you-must-put-some-deb-src-uris-in-your-sources-list
sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources

apt update

apt-get -y build-dep linux
apt-get -y install git-core libncurses5 libncurses5-dev libelf-dev asciidoc binutils-dev
apt-get -y install libssl-dev
apt -y install flex bison
apt -y install zstd

mkdir my-arm-kernel
cd my-arm-kernel
apt source linux-image-unsigned-$(uname -r)
cd linux-6.8.0
# cp /boot/config-$(uname -r) .config
make olddefconfig
make -j$(nproc)
