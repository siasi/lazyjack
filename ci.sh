#!/bin/sh

. /opt/dev-tools/python/Linux/2.7.4/python/bin/activate

usage ()
{
    echo "usage: $0 [options]"
    echo ""
    echo " options:"
    echo "  -h, --help       show this help message and exit"
    echo "  -c, --clean      remove installation then install again"
    exit 0
}

ANSIBLE_SSH_ARGS=""
export ANSIBLE_SSH_ARGS

PLAYBOOK=install.yml
if [ $# -eq 1 ]; then
    if [ "$1" == "-h" -o "$1" == "--help" ]; then
        usage
    fi
    if [ "$1" == "-c" -o "$1" == "--clean" ]; then
        PLAYBOOK=deploy.yml
    else
        echo "Option $1 not recognized. Exiting..."
        exit 1
    fi
fi

(cd %(dest)s/ansible && ansible-playbook --private-key=~/.ssh/ci_rsa -i hosts $PLAYBOOK)
