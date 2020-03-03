#!/bin/sh

. /opt/dev-tools/python/Linux/2.7.4/python/bin/activate

ANSIBLE_SSH_ARGS=""
export ANSIBLE_SSH_ARGS

(cd ~/etc/lazyjack && python install.py $*)
