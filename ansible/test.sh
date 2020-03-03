#!/bin/sh

. /opt/dev-tools/python/Linux/2.7.4/python/bin/activate

# Sanity tests for ansible.

ansible --private-key=~/.ssh/ci_rsa -i hosts all -m ping
ansible --private-key=~/.ssh/ci_rsa -i hosts all -u root -m ping
ansible --private-key=~/.ssh/ci_rsa -i hosts all -u root -a "cat /etc/shadow"
